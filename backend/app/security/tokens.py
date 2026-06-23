from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.models.auth import ExtensionDevice

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(user: User, token_type: str = "web", expires_delta: timedelta | None = None, device_id: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(days=settings.extension_token_days) if token_type == "extension" else timedelta(hours=settings.jwt_expire_hours)
    payload: dict[str, Any] = {
        "sub": str(user.id),
        "external_id": user.external_id,
        "email": user.email,
        "name": user.name,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if device_id:
        payload["device_id"] = device_id
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 만료되었습니다.") from error
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 인증 토큰입니다.") from error


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    payload = decode_token(credentials.credentials)
    user = db.query(User).filter(User.id == int(payload["sub"]), User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
    if payload.get("type") == "extension":
        device_id = str(payload.get("device_id") or "")
        device = db.query(ExtensionDevice).filter(
            ExtensionDevice.user_id == user.id,
            ExtensionDevice.device_id == device_id,
            ExtensionDevice.revoked.is_(False),
        ).first()
        if not device:
            raise HTTPException(status_code=401, detail="해제되었거나 유효하지 않은 확장 프로그램 연결입니다.")
    return user


def get_current_user(user: User | None = Depends(get_current_user_optional)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return user
