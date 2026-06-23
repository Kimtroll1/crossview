from __future__ import annotations

import hashlib
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.auth import DeviceLinkCode, ExtensionDevice
from app.models.report_subscription import ReportSubscription
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ExtensionExchangeRequest,
    ExtensionExchangeResponse,
    GoogleLoginRequest,
    LinkCodeResponse,
    LoginRequest,
    RegisterRequest,
    UserPublic,
)
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        externalId=user.external_id,
        email=user.email,
        name=user.name,
        avatarUrl=user.avatar_url,
        authProvider=user.auth_provider,
        timezone=user.timezone,
    )


def _ensure_subscription(db: Session, user: User) -> None:
    existing = db.query(ReportSubscription).filter(ReportSubscription.user_id == user.id).first()
    if not existing:
        db.add(ReportSubscription(user_id=user.id, email_address=user.email, email_enabled=bool(user.email)))


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")
    user = User(
        external_id=f"local:{uuid.uuid4().hex}",
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        auth_provider="local",
    )
    db.add(user)
    db.flush()
    _ensure_subscription(db, user)
    db.commit()
    db.refresh(user)
    return AuthResponse(accessToken=create_access_token(user), user=_user_public(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return AuthResponse(accessToken=create_access_token(user), user=_user_public(user))


@router.post("/google", response_model=AuthResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail="GOOGLE_CLIENT_ID가 설정되지 않았습니다.")
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        claims = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.google_client_id,
        )
    except Exception as error:
        raise HTTPException(status_code=401, detail="Google 로그인 토큰을 확인할 수 없습니다.") from error

    google_sub = str(claims.get("sub") or "")
    email = str(claims.get("email") or "").lower() or None
    if not google_sub:
        raise HTTPException(status_code=401, detail="Google 사용자 식별자가 없습니다.")

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            external_id=f"google:{google_sub}",
            google_sub=google_sub,
            email=email,
            name=claims.get("name") or "CrossView 사용자",
            avatar_url=claims.get("picture"),
            auth_provider="google",
        )
        db.add(user)
        db.flush()
    else:
        user.google_sub = google_sub
        user.email = email or user.email
        user.name = claims.get("name") or user.name
        user.avatar_url = claims.get("picture") or user.avatar_url
        user.auth_provider = "google"
    _ensure_subscription(db, user)
    db.commit()
    db.refresh(user)
    return AuthResponse(accessToken=create_access_token(user), user=_user_public(user))


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(get_current_user)):
    return _user_public(user)


@router.post("/link-code", response_model=LinkCodeResponse)
def create_link_code(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alphabet = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(alphabet) for _ in range(6))
    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.add(DeviceLinkCode(user_id=user.id, code_hash=code_hash, expires_at=expires_at))
    db.commit()
    return LinkCodeResponse(code=code, expiresInSeconds=600)


@router.post("/extension/exchange", response_model=ExtensionExchangeResponse)
def exchange_extension_code(payload: ExtensionExchangeRequest, db: Session = Depends(get_db)):
    normalized = payload.code.upper().replace("-", "").strip()
    code_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)
    link = (
        db.query(DeviceLinkCode)
        .filter(
            DeviceLinkCode.code_hash == code_hash,
            DeviceLinkCode.consumed_at.is_(None),
            DeviceLinkCode.expires_at > now,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=400, detail="연결 코드가 잘못되었거나 만료되었습니다.")
    user = db.query(User).filter(User.id == link.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    device_id = uuid.uuid4().hex
    device = ExtensionDevice(user_id=user.id, device_id=device_id, label=payload.deviceLabel[:120])
    link.consumed_at = now
    db.add(device)
    db.commit()
    token = create_access_token(user, token_type="extension", device_id=device_id)
    return ExtensionExchangeResponse(
        accessToken=token,
        user=_user_public(user),
        deviceId=device_id,
    )
