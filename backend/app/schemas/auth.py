from pydantic import BaseModel, EmailStr, Field


class UserPublic(BaseModel):
    id: int
    externalId: str
    email: str | None = None
    name: str | None = None
    avatarUrl: str | None = None
    authProvider: str
    timezone: str


class AuthResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    user: UserPublic


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str


class LinkCodeResponse(BaseModel):
    code: str
    expiresInSeconds: int


class ExtensionExchangeRequest(BaseModel):
    code: str
    deviceLabel: str = "Chrome Extension"


class ExtensionExchangeResponse(AuthResponse):
    deviceId: str
