"""Run hourly from cron: python scripts/send_due_reports.py"""
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal, init_db  # noqa: E402
from app.models.report_subscription import ReportSubscription  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.subscription_service import SubscriptionService  # noqa: E402


def main() -> int:
    init_db()
    db = SessionLocal()
    service = SubscriptionService()
    sent = 0
    try:
        subscriptions = db.query(ReportSubscription).filter(ReportSubscription.enabled.is_(True)).all()
        now = datetime.now(timezone.utc)
        for subscription in subscriptions:
            if not service.is_due(subscription, now):
                continue
            user = db.query(User).filter(User.id == subscription.user_id, User.is_active.is_(True)).first()
            if not user:
                continue
            results = service.deliver(db, user, subscription)
            print(user.external_id, [item.model_dump() for item in results])
            sent += 1
        print(f"CrossView report worker complete: {sent} subscription(s)")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
