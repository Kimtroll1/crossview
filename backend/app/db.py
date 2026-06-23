from __future__ import annotations

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings

_engine_kwargs: dict = {"pool_pre_ping": True}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    if settings.database_url.endswith(":memory:"):
        _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_postgres_columns() -> None:
    if engine.dialect.name != "postgresql":
        return
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    migrations: dict[str, dict[str, str]] = {
        "users": {
            "password_hash": "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255)",
            "google_sub": "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub VARCHAR(255)",
            "avatar_url": "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1000)",
            "auth_provider": "ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(40) DEFAULT 'local'",
            "timezone": "ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(80) DEFAULT 'Asia/Seoul'",
            "is_active": "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE",
            "updated_at": "ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
        },
        "analyses": {
            "bias_criteria": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS bias_criteria JSONB DEFAULT '[]'::jsonb",
            "bias_confidence": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS bias_confidence DOUBLE PRECISION DEFAULT 0",
            "bias_signals": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS bias_signals JSONB DEFAULT '{}'::jsonb",
            "comment_flow": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS comment_flow JSONB DEFAULT '{}'::jsonb",
            "issue": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS issue VARCHAR(255) DEFAULT '핵심 이슈'",
            "search_queries": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS search_queries JSONB DEFAULT '{}'::jsonb",
            "provider": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS provider VARCHAR(40) DEFAULT 'mock'",
            "model_name": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS model_name VARCHAR(120) DEFAULT ''",
            "prompt_version": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS prompt_version VARCHAR(80) DEFAULT 'crossview-bias-v2'",
            "updated_at": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW()",
            "resources_updated_at": "ALTER TABLE analyses ADD COLUMN IF NOT EXISTS resources_updated_at TIMESTAMPTZ",
        },
        "recommendations": {
            "published_at": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS published_at VARCHAR(80)",
            "thumbnail_url": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS thumbnail_url TEXT",
            "stance_score": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS stance_score INTEGER DEFAULT 0",
            "stance_label": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS stance_label VARCHAR(120) DEFAULT '관점 미분류'",
            "relevance_score": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS relevance_score DOUBLE PRECISION DEFAULT 0",
            "credibility_score": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS credibility_score DOUBLE PRECISION DEFAULT 0",
            "recommendation_reason": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS recommendation_reason TEXT",
            "key_point": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS key_point TEXT",
            "domain": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS domain VARCHAR(255)",
            "verified_url": "ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS verified_url BOOLEAN DEFAULT FALSE",
        },
    }
    with engine.begin() as connection:
        for table, columns in migrations.items():
            if table not in tables:
                continue
            existing = {column["name"] for column in inspector.get_columns(table)}
            for column_name, statement in columns.items():
                if column_name not in existing:
                    connection.execute(text(statement))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_sub_unique ON users (google_sub) WHERE google_sub IS NOT NULL"))
        connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_unique ON users (email) WHERE email IS NOT NULL"))


def init_db() -> None:
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _ensure_postgres_columns()
