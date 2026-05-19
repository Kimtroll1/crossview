import os
from fastapi import APIRouter
from app.schemas.analysis import VideoContext, AnalysisResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(video: VideoContext):
    provider = os.getenv("AI_PROVIDER", "mock")
    service = AIService(provider=provider)
    return await service.analyze_video(video)
