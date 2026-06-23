from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session

from app.models.report_subscription import ReportDelivery, ReportSubscription
from app.models.user import User
from app.schemas.settings import DeliveryResult
from app.security.secrets import decrypt_secret
from app.services.delivery_service import DeliveryService
from app.services.report_service import ReportService


class SubscriptionService:
    def is_due(self, subscription: ReportSubscription, now_utc: datetime | None = None) -> bool:
        if not subscription.enabled:
            return False
        now_utc = now_utc or datetime.now(timezone.utc)
        try:
            local_now = now_utc.astimezone(ZoneInfo(subscription.timezone or "Asia/Seoul"))
        except Exception:
            local_now = now_utc.astimezone(ZoneInfo("Asia/Seoul"))
        if local_now.hour != subscription.send_hour:
            return False
        if subscription.cadence == "weekly" and local_now.weekday() != subscription.weekday:
            return False
        if subscription.cadence == "monthly" and local_now.day != subscription.month_day:
            return False
        if subscription.last_sent_at:
            last_sent = subscription.last_sent_at
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)
            elapsed_hours = (now_utc - last_sent).total_seconds() / 3600
            if subscription.cadence == "weekly" and elapsed_hours < 120:
                return False
            if subscription.cadence == "monthly" and elapsed_hours < 600:
                return False
        return True

    def deliver(self, db: Session, user: User, subscription: ReportSubscription) -> list[DeliveryResult]:
        period = subscription.cadence if subscription.cadence in {"weekly", "monthly"} else "weekly"
        report = ReportService().build_report(db, user, period)
        sender = DeliveryService()
        results: list[DeliveryResult] = []

        def execute(channel: str, callback):
            try:
                detail = str(callback())[:900]
                results.append(DeliveryResult(channel=channel, success=True, detail=detail))
                db.add(ReportDelivery(user_id=user.id, period=period, channel=channel, status="sent", detail=detail))
            except Exception as error:
                detail = str(error)[:900]
                results.append(DeliveryResult(channel=channel, success=False, detail=detail))
                db.add(ReportDelivery(user_id=user.id, period=period, channel=channel, status="failed", detail=detail))

        if subscription.email_enabled and subscription.email_address:
            execute("email", lambda: sender.send_email(subscription.email_address, report))
        if subscription.slack_enabled:
            webhook = decrypt_secret(subscription.slack_webhook_encrypted)
            if webhook:
                execute("slack", lambda: sender.send_slack(webhook, report))
        if subscription.discord_enabled:
            webhook = decrypt_secret(subscription.discord_webhook_encrypted)
            if webhook:
                execute("discord", lambda: sender.send_discord(webhook, report))

        subscription.last_sent_at = datetime.now(timezone.utc)
        db.commit()
        return results
