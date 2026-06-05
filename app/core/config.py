import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────
    APP_NAME: str = "Vorgo"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production"

    # ── Database ──────────────────────────────────────────────────────────
    # asyncpg driver required - sync psycopg2 এ async কাজ করবে না
    DATABASE_URL: str = (
        "postgresql+asyncpg://vorgo_user:vorgo_pass@localhost:5432/vorgo_db"
    )

    # ── Redis ─────────────────────────────────────────────────────────────
    # refresh token, rate limiting, session revocation সব এখানে
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT - ED25519 ─────────────────────────────────────────────────────
    # keys খালি থাকলে app চলবে কিন্তু auth কাজ করবে না
    # `make generate-keys` চালালে .env এ automatically লিখে দেবে
    ED25519_PRIVATE_KEY: str = ""
    ED25519_PUBLIC_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # short - refresh token দিয়ে renew হবে
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Email ─────────────────────────────────────────────────────────────
    # EMAIL_PROVIDER: smtp | sendgrid | resend
    # production এ sendgrid বা resend নাও, smtp deliverability কম
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    # ── Stripe ────────────────────────────────────────────────────────────
    # STRIPE_WEBHOOK_SECRET ছাড়া webhook verify হবে না - সব event skip হবে
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ── Storage ───────────────────────────────────────────────────────────
    # AWS S3 বা Cloudflare R2 দুটোই চলবে - endpoint URL বদলালেই হবে
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION: str = "us-east-1"

    # ── AI ────────────────────────────────────────────────────────────────
    # যেটা use করবে সেটা দাও, বাকিগুলো খালি রাখলেও চলবে
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── Observability ─────────────────────────────────────────────────────
    SENTRY_DSN: str = ""  # খালি থাকলে Sentry initialize হবে না

    # ── 2FA ───────────────────────────────────────────────────────────────
    # AES-256 key - TOTP secret encrypt করে store করতে লাগে
    # `python -c "import secrets; print(secrets.token_hex(32))"` দিয়ে generate করো
    TOTP_ENCRYPTION_KEY: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"
    # .env এ JSON array হিসেবে দাও: ["http://localhost:3000","https://app.yourdomain.com"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        # .env থেকে string হিসেবে আসে, JSON parse করে list বানাও
        # JSON fail করলে comma-separated fallback
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [i.strip() for i in v.split(",")]
        return v

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# module-level singleton - সব জায়গা থেকে `from app.core.config import settings` দিয়ে import করো
settings = Settings()
