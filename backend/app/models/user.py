from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(120), nullable=True)
    password_hash = Column(String(255), nullable=True)
    google_sub = Column(String(255), unique=True, index=True, nullable=True)
    avatar_url = Column(String(1000), nullable=True)
    auth_provider = Column(String(40), default="local", nullable=False)
    timezone = Column(String(80), default="Asia/Seoul", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
