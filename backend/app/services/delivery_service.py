from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from urllib.parse import urlparse
import httpx

from app.config import settings
from app.schemas.report import ReportResponse


class DeliveryService:
    def render_text(self, report: ReportResponse) -> str:
        signal = report.signalAverages
        topics = ", ".join(report.topTopics) if report.topTopics else "기록 없음"
        return (
            f"CrossView {('월간' if report.period == 'monthly' else '주간')} 리포트\n"
            f"분석 영상: {report.totalVideos}개 · 정치/시사: {report.politicalVideos}개\n"
            f"좌/중립/우: {report.leftRatio}% / {report.neutralRatio}% / {report.rightRatio}%\n"
            f"평균 편향도: {report.averageBiasScore:+.2f} · AI 의심: {report.aiRiskRatio}%\n"
            f"감정·선동 {signal.emotionalManipulation:.1f}/5 · 선택적 근거 {signal.evidenceSelection:.1f}/5\n"
            f"관점 누락 {signal.viewpointOmission:.1f}/5 · 출처 편중 {signal.sourceConcentration:.1f}/5\n"
            f"다른 관점 탐색률: {report.alternativeExplorationRate}%\n"
            f"주요 주제: {topics}\n\n"
            f"CrossView 제안: {report.suggestion}\n"
            f"리포트 보기: {settings.frontend_url}/dashboard"
        )

    def render_html(self, report: ReportResponse) -> str:
        text = self.render_text(report)
        lines = "".join(f"<p style='margin:7px 0'>{escape(line)}</p>" for line in text.splitlines() if line)
        resources = "".join(
            f"<li style='margin:9px 0'><a href='{escape(item.url)}'>{escape(item.title)}</a> — {escape(item.stanceLabel)}</li>"
            for item in report.recommendedResources[:4]
        )
        resource_block = f"<h3>균형을 위한 자료</h3><ul>{resources}</ul>" if resources else ""
        return f"""
        <div style="font-family:Arial,'Noto Sans KR',sans-serif;max-width:640px;margin:auto;color:#0f172a">
          <div style="padding:24px;background:#0f172a;color:white;border-radius:18px 18px 0 0">
            <h1 style="margin:0">CrossView 리포트</h1>
            <p style="margin:8px 0 0;color:#bfdbfe">판단을 대신하지 않고, 더 많은 관점을 확인하도록 돕습니다.</p>
          </div>
          <div style="padding:24px;border:1px solid #e2e8f0;border-top:0;border-radius:0 0 18px 18px">
            {lines}
            {resource_block}
          </div>
        </div>
        """

    def send_email(self, to: str, report: ReportResponse) -> str:
        if not settings.resend_api_key:
            raise RuntimeError("RESEND_API_KEY가 설정되지 않았습니다.")
        import resend

        resend.api_key = settings.resend_api_key
        response = resend.Emails.send({
            "from": settings.report_from_email,
            "to": [to],
            "subject": f"CrossView {('월간' if report.period == 'monthly' else '주간')} 미디어 리포트",
            "html": self.render_html(report),
        })
        return str(response)

    def send_slack(self, webhook_url: str, report: ReportResponse) -> str:
        self._validate_webhook(webhook_url, "slack")
        response = httpx.post(webhook_url, json={"text": self.render_text(report)}, timeout=15)
        response.raise_for_status()
        return response.text or "ok"

    def send_discord(self, webhook_url: str, report: ReportResponse) -> str:
        self._validate_webhook(webhook_url, "discord")
        text = self.render_text(report)
        response = httpx.post(
            webhook_url,
            json={
                "username": "CrossView",
                "embeds": [{
                    "title": f"CrossView {('월간' if report.period == 'monthly' else '주간')} 리포트",
                    "description": text[:4000],
                    "url": f"{settings.frontend_url}/dashboard",
                    "color": 2466010,
                }],
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.text or "ok"

    @staticmethod
    def _validate_webhook(url: str, channel: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError("Webhook은 HTTPS 주소여야 합니다.")
        host = parsed.netloc.lower()
        if channel == "slack" and host not in {"hooks.slack.com", "hooks.slack-gov.com"}:
            raise ValueError("Slack Incoming Webhook 주소가 아닙니다.")
        if channel == "discord" and host not in {"discord.com", "discordapp.com"}:
            raise ValueError("Discord Webhook 주소가 아닙니다.")
