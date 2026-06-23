from pydantic import BaseModel, EmailStr, Field


class ReportSettingsUpdate(BaseModel):
    enabled: bool = False
    cadence: str = Field(default="weekly", pattern="^(weekly|monthly)$")
    timezone: str = "Asia/Seoul"
    sendHour: int = Field(default=9, ge=0, le=23)
    weekday: int = Field(default=0, ge=0, le=6)
    monthDay: int = Field(default=1, ge=1, le=28)
    emailEnabled: bool = True
    emailAddress: EmailStr | None = None
    slackEnabled: bool = False
    slackWebhook: str | None = None
    discordEnabled: bool = False
    discordWebhook: str | None = None


class ReportSettingsResponse(BaseModel):
    enabled: bool
    cadence: str
    timezone: str
    sendHour: int
    weekday: int
    monthDay: int
    emailEnabled: bool
    emailAddress: str | None = None
    slackEnabled: bool
    slackWebhookMasked: str = ""
    discordEnabled: bool
    discordWebhookMasked: str = ""


class DeliveryResult(BaseModel):
    channel: str
    success: bool
    detail: str = ""
