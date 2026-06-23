from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.analysis import Analysis
from app.models.user import User
from app.models.video import Video
from app.models.watch_history import WatchHistory
from app.schemas.history import HistoryItem, HistoryResponse
from app.security.tokens import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])


def _build_history(db: Session, user: User) -> HistoryResponse:
    rows = (
        db.query(WatchHistory, Video, Analysis)
        .join(Video, WatchHistory.video_id == Video.id)
        .join(Analysis, WatchHistory.analysis_id == Analysis.id)
        .filter(WatchHistory.user_id == user.id)
        .order_by(WatchHistory.watched_at.desc())
        .limit(200)
        .all()
    )
    items = [
        HistoryItem(
            watchedAt=watch.watched_at.isoformat(),
            videoId=video.youtube_video_id,
            title=video.title,
            channelName=video.channel_name or "",
            url=video.url,
            isPolitical=bool(analysis.is_political),
            biasScore=analysis.bias_score or 0,
            biasLabel=analysis.bias_label or "중립에 가까움",
            biasConfidence=float(analysis.bias_confidence or 0),
            biasCriteria=analysis.bias_criteria or [],
            biasSignals=analysis.bias_signals or {},
            commentFlow=analysis.comment_flow or {},
            aiRisk=analysis.ai_risk or "low",
            issue=analysis.issue or "핵심 이슈",
            summary=analysis.summary,
        )
        for watch, video, analysis in rows[:50]
    ]
    return HistoryResponse(userId=user.external_id, items=items)


@router.get("/me", response_model=HistoryResponse)
def get_my_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _build_history(db, user)


@router.get("/{user_id}", response_model=HistoryResponse)
def get_legacy_history(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.external_id == user_id).first()
    if not user:
        return HistoryResponse(userId=user_id)
    return _build_history(db, user)
