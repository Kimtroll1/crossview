from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from app.db import Base


class ResourceClick(Base):
    __tablename__ = "resource_clicks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id"), nullable=False, index=True)
    category = Column(String(40), nullable=False)
    clicked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
