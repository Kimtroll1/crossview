from __future__ import annotations

import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings


def _fernet() -> Fernet:
    if settings.secrets_encryption_key:
        key = settings.secrets_encryption_key.encode("utf-8")
    else:
        key = base64.urlsafe_b64encode(hashlib.sha256(settings.jwt_secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None


def mask_secret(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 12:
        return "••••••••"
    return f"{value[:8]}…{value[-6:]}"
