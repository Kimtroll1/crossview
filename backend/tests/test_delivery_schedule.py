from datetime import datetime, timedelta, timezone

import pytest

from app.models.report_subscription import ReportSubscription
from app.services.delivery_service import DeliveryService
from app.services.subscription_service import SubscriptionService


def test_weekly_subscription_is_due_in_user_timezone():
    subscription = ReportSubscription(
        enabled=True,
        cadence="weekly",
        timezone="Asia/Seoul",
        send_hour=9,
        weekday=0,
        month_day=1,
    )
    monday_9am_seoul = datetime(2026, 6, 22, 0, 0, tzinfo=timezone.utc)
    assert SubscriptionService().is_due(subscription, monday_9am_seoul) is True

    subscription.last_sent_at = monday_9am_seoul - timedelta(hours=24)
    assert SubscriptionService().is_due(subscription, monday_9am_seoul) is False


def test_webhook_host_validation_blocks_untrusted_urls():
    DeliveryService._validate_webhook("https://hooks.slack.com/services/T/B/X", "slack")
    DeliveryService._validate_webhook("https://discord.com/api/webhooks/1/token", "discord")
    with pytest.raises(ValueError):
        DeliveryService._validate_webhook("https://example.com/fake", "slack")
    with pytest.raises(ValueError):
        DeliveryService._validate_webhook("http://discord.com/api/webhooks/1/token", "discord")
