import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import asyncio

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models.analysis import Analysis
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.video import Video  # noqa: F401
from app.models.watch_history import WatchHistory  # noqa: F401
from app.schemas.analysis import VideoContext
from app.services.ai_service import AIService
from app.services.storage_service import StorageService


def sample_video(force_refresh: bool = False) -> VideoContext:
    return VideoContext(
        userId="test-user",
        videoId="consistency-video",
        url="https://www.youtube.com/watch?v=consistency-video",
        title="대통령 정책에 대한 여야 반응 분석",
        channelName="테스트 채널",
        description="정부 정책과 여야 반응을 다루는 정치 영상입니다.",
        transcript="정부 정책의 장점과 비판을 함께 설명합니다.",
        commentsText="1. 정책을 지지합니다.\n2. 반대 근거도 확인해야 합니다.",
        commentsCount=2,
        analysisSource="transcript+comments+description",
        forceRefresh=force_refresh,
    )


def test_mock_analysis_is_deterministic():
    service = AIService(provider="mock")
    first = asyncio.run(service.analyze_video(sample_video()))
    second = asyncio.run(service.analyze_video(sample_video()))

    assert first.biasScore == second.biasScore
    assert first.biasCriteria == second.biasCriteria
    assert first.biasConfidence == second.biasConfidence
    assert first.aiRisk == second.aiRisk


def test_video_id_cache_returns_same_persisted_analysis():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    service = AIService(provider="mock")
    storage = StorageService()
    video = sample_video()
    result = asyncio.run(service.analyze_video(video))
    storage.save_analysis(db, video, result)

    cached = storage.get_cached_analysis(db, video.videoId)
    assert cached is not None
    assert cached.cached is True
    assert cached.biasScore == result.biasScore
    assert cached.biasCriteria == result.biasCriteria
    assert db.query(Analysis).count() == 1
