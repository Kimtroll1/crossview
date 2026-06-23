import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("JWT_SECRET", "crossview-test-secret")

from fastapi.testclient import TestClient

import app.models  # noqa: F401
from app.db import Base, engine
from app.main import app


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_full_account_extension_analysis_report_flow():
    with TestClient(app) as client:
        registered = client.post(
            "/api/auth/register",
            json={"email": "demo@example.com", "password": "strong-pass-123", "name": "데모 사용자"},
        )
        assert registered.status_code == 200, registered.text
        token = registered.json()["accessToken"]

        me = client.get("/api/auth/me", headers=auth_header(token))
        assert me.status_code == 200
        assert me.json()["email"] == "demo@example.com"

        link = client.post("/api/auth/link-code", headers=auth_header(token))
        assert link.status_code == 200
        assert len(link.json()["code"]) == 6

        exchange = client.post(
            "/api/auth/extension/exchange",
            json={"code": link.json()["code"], "deviceLabel": "Test Chrome"},
        )
        assert exchange.status_code == 200, exchange.text
        extension_token = exchange.json()["accessToken"]

        payload = {
            "userId": "ignored-demo-id",
            "videoId": "integration-video",
            "url": "https://www.youtube.com/watch?v=integration-video",
            "title": "정부 정책에 대한 여야 반응",
            "channelName": "테스트 채널",
            "description": "정부 정책의 장점과 비판을 함께 다룹니다.",
            "transcript": "정부 정책을 지지하는 주장과 반대 측 반론을 소개합니다.",
            "commentsText": "정책을 지지합니다.\n반대 근거도 확인해야 합니다.",
            "commentsCount": 2,
            "analysisSource": "transcript+comments+description",
        }
        first = client.post("/api/analyze", json=payload, headers=auth_header(extension_token))
        assert first.status_code == 200, first.text
        body = first.json()
        assert body["cached"] is False
        assert set(body["biasSignals"]) == {
            "emotionalManipulation",
            "evidenceSelection",
            "viewpointOmission",
            "sourceConcentration",
        }
        assert "commentFlow" in body

        second = client.post("/api/analyze", json=payload, headers=auth_header(extension_token))
        assert second.status_code == 200
        assert second.json()["cached"] is True

        history = client.get("/api/history/me", headers=auth_header(token))
        assert history.status_code == 200
        assert len(history.json()["items"]) == 1
        assert history.json()["items"][0]["videoId"] == "integration-video"

        report = client.get("/api/reports/me?period=weekly", headers=auth_header(token))
        assert report.status_code == 200
        assert report.json()["totalVideos"] == 1
        assert "signalAverages" in report.json()

        settings = client.put(
            "/api/settings/report",
            headers=auth_header(token),
            json={
                "enabled": True,
                "cadence": "weekly",
                "timezone": "Asia/Seoul",
                "sendHour": 9,
                "weekday": 0,
                "monthDay": 1,
                "emailEnabled": True,
                "emailAddress": "demo@example.com",
                "slackEnabled": False,
                "discordEnabled": False,
            },
        )
        assert settings.status_code == 200, settings.text
        assert settings.json()["enabled"] is True


def test_duplicate_registration_and_protected_route():
    with TestClient(app) as client:
        payload = {"email": "duplicate@example.com", "password": "strong-pass-123", "name": "중복"}
        assert client.post("/api/auth/register", json=payload).status_code == 200
        assert client.post("/api/auth/register", json=payload).status_code == 409
        assert client.get("/api/reports/me").status_code == 401
