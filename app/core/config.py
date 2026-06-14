import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Vorgo"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"

    # asyncpg driver required - do not switch to sync psycopg2
    DATABASE_URL: str = (
        "postgresql+asyncpg://vorgo_user:vorgo_pass@localhost:5432/vorgo_db"
    )

    # used for refresh tokens, rate limiting, and session revocation
    REDIS_URL: str = "redis://localhost:6379/0"

    # ED25519 keys - leave empty to start, run `make generate-keys` to populate
    ED25519_PRIVATE_KEY: str = ""
    ED25519_PUBLIC_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # EMAIL_PROVIDER: smtp | sendgrid | resend
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    # Billing Provider - stripe | lemonsqueezy | paypal | payoneer
    BILLING_PROVIDER: str = "stripe"

    # Stripe - webhook secret required for webhook verification
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_FREE_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""

    # Lemon Squeezy settings
    LEMON_SQUEEZY_API_KEY: str = ""
    LEMON_SQUEEZY_WEBHOOK_SECRET: str = ""
    LEMON_SQUEEZY_FREE_PRICE_ID: str = ""
    LEMON_SQUEEZY_PRO_PRICE_ID: str = ""
    LEMON_SQUEEZY_ENTERPRISE_PRICE_ID: str = ""

    # PayPal settings
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_MODE: str = "sandbox"  # sandbox | live
    PAYPAL_FREE_PLAN_ID: str = ""
    PAYPAL_PRO_PLAN_ID: str = ""
    PAYPAL_ENTERPRISE_PLAN_ID: str = ""

    # Payoneer settings
    PAYONEER_CLIENT_ID: str = ""
    PAYONEER_CLIENT_SECRET: str = ""

    # S3-compatible storage - works with AWS S3 and Cloudflare R2
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "us-east-1"

    # AI providers - set whichever you use, leave others empty
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # Sentry - leave empty to disable
    SENTRY_DSN: str = ""

    # AES-256 key for encrypting TOTP secrets at rest
    # generate: python -c "import secrets; print(secrets.token_hex(32))"
    TOTP_ENCRYPTION_KEY: str = ""

    FRONTEND_URL: str = "http://localhost:3000"
    # set as JSON array in .env: ["http://localhost:3000","https://app.yourdomain.com"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",")]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
