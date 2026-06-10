from pydantic import BaseModel


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TwoFactorSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str


class TwoFactorVerifyRequest(BaseModel):
    code: str


class TwoFactorVerifyResponse(BaseModel):
    backup_codes: list[str]


class TwoFactorChallengeRequest(BaseModel):
    pre_2fa_token: str
    code: str


class LoginResponse2FA(BaseModel):
    requires_2fa: bool = True
    pre_2fa_token: str


