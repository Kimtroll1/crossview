from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_version: str = "2.0.0"
    environment: str = "development"
    frontend_url: str = "http://localhost:3000"

    ai_provider: str = "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_search_model: str = "gemini-3.1-flash-lite"
    enable_gemini_search: bool = True
    enable_url_context: bool = True
    resource_cache_hours: int = 24
    youtube_api_key: str = ""
    prompt_version: str = "crossview-bias-v2"

    database_url: str = "postgresql+psycopg2://crossview:crossview@localhost:5432/crossview"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://www.youtube.com,https://youtube.com"

    jwt_secret: str = "change-this-development-secret"
    jwt_expire_hours: int = 24 * 14
    extension_token_days: int = 180
    google_client_id: str = ""
    secrets_encryption_key: str = ""

    resend_api_key: str = ""
    report_from_email: str = "CrossView <onboarding@resend.dev>"
    report_worker_key: str = "change-this-worker-key"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
