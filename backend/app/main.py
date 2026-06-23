from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routes.analyze import router as analyze_router
from app.routes.auth import router as auth_router
from app.routes.history import router as history_router
from app.routes.reports import router as reports_router
from app.routes.resources import router as resources_router
from app.routes.settings import router as settings_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="CrossView API", version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth_router, analyze_router, history_router, reports_router, resources_router, settings_router):
    app.include_router(router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "CrossView API",
        "version": settings.app_version,
        "features": ["auth", "extension-link", "bias-signals", "real-resource-search", "personal-reports", "scheduled-delivery"],
    }


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "CrossView API",
        "version": settings.app_version,
        "provider": settings.ai_provider,
        "model": settings.gemini_model if settings.ai_provider == "gemini" else "mock",
        "youtubeSearch": bool(settings.youtube_api_key),
        "webSearch": bool(settings.ai_provider == "gemini" and settings.gemini_api_key and settings.enable_gemini_search),
        "urlContext": bool(settings.ai_provider == "gemini" and settings.gemini_api_key and settings.enable_url_context),
        "emailDelivery": bool(settings.resend_api_key),
    }
