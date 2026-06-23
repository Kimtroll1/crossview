from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import relationship
from app.db import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    main_claims = Column(JSON, default=list)
    evidence_summary = Column(Text, nullable=True)
    caution_points = Column(JSON, default=list)

    is_political = Column(Boolean, default=False)
    bias_score = Column(Integer, default=0)
    bias_label = Column(String(120), default="중립에 가까움")
    bias_summary = Column(Text, nullable=True)
    bias_criteria = Column(JSON, default=list)
    bias_confidence = Column(Float, default=0.0)
    bias_signals = Column(JSON, default=dict)

    ai_risk = Column(String(30), default="low")
    ai_summary = Column(Text, nullable=True)
    comment_flow = Column(JSON, default=dict)
    comment_mood = Column(String(120), nullable=True)
    comment_intensity = Column(String(60), nullable=True)
    comment_leaning = Column(String(120), nullable=True)
    comment_warning_signals = Column(JSON, default=list)

    source_used = Column(String(120), default="metadata")
    source_label = Column(String(255), default="제목·채널 메타데이터")
    comments_count = Column(Integer, default=0)
    issue = Column(String(255), default="핵심 이슈")
    search_queries = Column(JSON, default=dict)

    provider = Column(String(40), default="mock")
    model_name = Column(String(120), default="")
    prompt_version = Column(String(80), default="crossview-bias-v2")
    raw_result = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    resources_updated_at = Column(DateTime(timezone=True), nullable=True)

    video = relationship("Video")
