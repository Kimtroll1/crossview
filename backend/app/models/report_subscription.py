from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from app.db import Base


class ReportSubscription(Base):
    __tablename__ = "report_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=False, nullable=False)
    cadence = Column(String(20), default="weekly", nullable=False)
    timezone = Column(String(80), default="Asia/Seoul", nullable=False)
    send_hour = Column(Integer, default=9, nullable=False)
    weekday = Column(Integer, default=0, nullable=False)
    month_day = Column(Integer, default=1, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    email_address = Column(String(255), nullable=True)
    slack_enabled = Column(Boolean, default=False, nullable=False)
    slack_webhook_encrypted = Column(String(3000), nullable=True)
    discord_enabled = Column(Boolean, default=False, nullable=False)
    discord_webhook_encrypted = Column(String(3000), nullable=True)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ReportDelivery(Base):
    __tablename__ = "report_deliveries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    period = Column(String(20), nullable=False)
    channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    detail = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
