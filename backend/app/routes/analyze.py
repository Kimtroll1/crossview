from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.analysis import AnalysisResponse, VideoContext
from app.security.tokens import get_current_user_optional
from app.services.ai_service import AIService
from app.services.search_service import SearchService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(
    video: VideoContext,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    storage = StorageService()
    if current_user:
        video.userId = current_user.external_id

    if video.videoId and not video.forceRefresh:
        cached = storage.get_cached_analysis(db, video.videoId)
        if cached is not None:
            search_configured = bool(
                settings.youtube_api_key
                or (settings.ai_provider == "gemini" and settings.gemini_api_key and settings.enable_gemini_search)
            )
            should_refresh_resources = video.refreshResources or (
                search_configured and storage.resources_stale(db, video.videoId, settings.resource_cache_hours)
            )
            if should_refresh_resources:
                refreshed = await SearchService().enrich(video, cached)
                cached = storage.replace_resources(db, video.videoId, refreshed)
                cached.resourcesCached = False
            storage.record_cached_view(db, video, cached, current_user)
            return cached

    result = await AIService(provider=settings.ai_provider).analyze_video(video)
    result = await SearchService().enrich(video, result)
    try:
        return storage.save_analysis(db, video, result, current_user)
    except Exception as error:
        db.rollback()
        print(f"[CrossView] DB save failed. Analysis still returned. Error: {error}")
        return result


@router.post("/videos/{video_id}/resources/refresh", response_model=AnalysisResponse)
async def refresh_resources(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    storage = StorageService()
    cached = storage.get_cached_analysis(db, video_id)
    video_model = db.query(Video).filter(Video.youtube_video_id == video_id).first()
    if cached is None or video_model is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="분석된 영상을 찾을 수 없습니다.")
    context = VideoContext(
        userId=current_user.external_id if current_user else "demo-user",
        videoId=video_id,
        url=video_model.url,
        title=video_model.title,
        channelName=video_model.channel_name or "",
        description=video_model.description or "",
    )
    refreshed = await SearchService().enrich(context, cached)
    return storage.replace_resources(db, video_id, refreshed)
