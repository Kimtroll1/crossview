from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from app.db import Base


class DeviceLinkCode(Base):
    __tablename__ = "device_link_codes"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String(128), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExtensionDevice(Base):
    __tablename__ = "extension_devices"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(120), unique=True, index=True, nullable=False)
    label = Column(String(120), default="Chrome Extension")
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
