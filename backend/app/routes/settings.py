from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.report_subscription import ReportSubscription
from app.models.user import User
from app.schemas.settings import DeliveryResult, ReportSettingsResponse, ReportSettingsUpdate
from app.security.secrets import decrypt_secret, encrypt_secret, mask_secret
from app.security.tokens import get_current_user
from app.services.delivery_service import DeliveryService
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/settings", tags=["settings"])


def _get_or_create(db: Session, user: User) -> ReportSubscription:
    item = db.query(ReportSubscription).filter(ReportSubscription.user_id == user.id).first()
    if not item:
        item = ReportSubscription(user_id=user.id, email_address=user.email, email_enabled=bool(user.email))
        db.add(item)
        db.commit()
        db.refresh(item)
    return item


def _response(item: ReportSubscription) -> ReportSettingsResponse:
    return ReportSettingsResponse(
        enabled=item.enabled,
        cadence=item.cadence,
        timezone=item.timezone,
        sendHour=item.send_hour,
        weekday=item.weekday,
        monthDay=item.month_day,
        emailEnabled=item.email_enabled,
        emailAddress=item.email_address,
        slackEnabled=item.slack_enabled,
        slackWebhookMasked=mask_secret(decrypt_secret(item.slack_webhook_encrypted)),
        discordEnabled=item.discord_enabled,
        discordWebhookMasked=mask_secret(decrypt_secret(item.discord_webhook_encrypted)),
    )


@router.get("/report", response_model=ReportSettingsResponse)
def get_report_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _response(_get_or_create(db, user))


@router.put("/report", response_model=ReportSettingsResponse)
def update_report_settings(
    payload: ReportSettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = _get_or_create(db, user)
    email_address = str(payload.emailAddress) if payload.emailAddress else user.email
    has_slack = bool(payload.slackWebhook or item.slack_webhook_encrypted)
    has_discord = bool(payload.discordWebhook or item.discord_webhook_encrypted)
    if payload.slackEnabled and not has_slack:
        raise HTTPException(status_code=400, detail="Slack Webhook URL을 입력해주세요.")
    if payload.discordEnabled and not has_discord:
        raise HTTPException(status_code=400, detail="Discord Webhook URL을 입력해주세요.")
    if payload.emailEnabled and not email_address:
        raise HTTPException(status_code=400, detail="리포트를 받을 이메일 주소를 입력해주세요.")
    if payload.enabled and not (
        (payload.emailEnabled and email_address)
        or (payload.slackEnabled and has_slack)
        or (payload.discordEnabled and has_discord)
    ):
        raise HTTPException(status_code=400, detail="리포트 전송 채널을 하나 이상 설정해주세요.")

    item.enabled = payload.enabled
    item.cadence = payload.cadence
    item.timezone = payload.timezone
    item.send_hour = payload.sendHour
    item.weekday = payload.weekday
    item.month_day = payload.monthDay
    item.email_enabled = payload.emailEnabled
    item.email_address = email_address
    item.slack_enabled = payload.slackEnabled
    item.discord_enabled = payload.discordEnabled
    if payload.slackWebhook:
        DeliveryService._validate_webhook(payload.slackWebhook, "slack")
        item.slack_webhook_encrypted = encrypt_secret(payload.slackWebhook)
    if payload.discordWebhook:
        DeliveryService._validate_webhook(payload.discordWebhook, "discord")
        item.discord_webhook_encrypted = encrypt_secret(payload.discordWebhook)
    db.commit()
    db.refresh(item)
    return _response(item)


@router.post("/report/test", response_model=list[DeliveryResult])
def test_report_delivery(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = _get_or_create(db, user)
    report = ReportService().build_report(db, user, item.cadence)
    sender = DeliveryService()
    results: list[DeliveryResult] = []

    def attempt(channel: str, callback):
        try:
            results.append(DeliveryResult(channel=channel, success=True, detail=str(callback())[:500]))
        except Exception as error:
            results.append(DeliveryResult(channel=channel, success=False, detail=str(error)[:500]))

    if item.email_enabled and item.email_address:
        attempt("email", lambda: sender.send_email(item.email_address, report))
    if item.slack_enabled:
        webhook = decrypt_secret(item.slack_webhook_encrypted)
        if webhook:
            attempt("slack", lambda: sender.send_slack(webhook, report))
    if item.discord_enabled:
        webhook = decrypt_secret(item.discord_webhook_encrypted)
        if webhook:
            attempt("discord", lambda: sender.send_discord(webhook, report))
    if not results:
        raise HTTPException(status_code=400, detail="활성화된 전송 채널이 없습니다.")
    return results
