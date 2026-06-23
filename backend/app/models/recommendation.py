from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from app.db import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    category = Column(String(40), nullable=False, index=True)
    resource_type = Column(String(40), nullable=False)
    title = Column(Text, nullable=False)
    url = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    published_at = Column(String(80), nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    stance_score = Column(Integer, default=0)
    stance_label = Column(String(120), default="관점 미분류")
    relevance_score = Column(Float, default=0.0)
    credibility_score = Column(Float, default=0.0)
    recommendation_reason = Column(Text, nullable=True)
    key_point = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    verified_url = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
