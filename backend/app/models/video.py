from sqlalchemy import Column, DateTime, Integer, String, Text, func

from app.db import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    youtube_video_id = Column(String(128), unique=True, index=True, nullable=False)
    title = Column(Text, nullable=False)
    channel_name = Column(String(255), nullable=True)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
