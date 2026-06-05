import base64
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from fastapi_users.authentication import JWTStrategy

from app.core.config import settings

# ── Key loaders ───────────────────────────────────────────────────────────────


def load_private_key() -> Ed25519PrivateKey:
    if not settings.ED25519_PRIVATE_KEY:
        raise ValueError("ED25519_PRIVATE_KEY is not set. Run `make generate-keys`.")
    raw = base64.b64decode(settings.ED25519_PRIVATE_KEY)
    return Ed25519PrivateKey.from_private_bytes(raw)


def load_public_key() -> Ed25519PublicKey:
    if not settings.ED25519_PUBLIC_KEY:
        raise ValueError("ED25519_PUBLIC_KEY is not set. Run `make generate-keys`.")
    raw = base64.b64decode(settings.ED25519_PUBLIC_KEY)
    return Ed25519PublicKey.from_public_bytes(raw)


# ── Token creators ────────────────────────────────────────────────────────────


def create_access_token(user_id: str) -> str:
    private_key = load_private_key()
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC)
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, private_key, algorithm="EdDSA")


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Returns (token, jti). jti is used as the Redis key."""
    private_key = load_private_key()
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "jti": jti,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    token = jwt.encode(payload, private_key, algorithm="EdDSA")
    return token, jti


def verify_token(token: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError on failure."""
    public_key = load_public_key()
    return jwt.decode(token, public_key, algorithms=["EdDSA"])


# ── fastapi-users strategy ────────────────────────────────────────────────────


class ED25519JWTStrategy(JWTStrategy):
    """
    fastapi-users JWTStrategy subclass.
    Only write_token and read_token are overridden - everything else stays.
    auth_backend in auth.py uses this instead of the default HS256 strategy.
    """

    def __init__(self) -> None:
        # parent __init__ needs a secret - not used since we override sign/verify
        super().__init__(
            secret="not-used",
            lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def write_token(self, user) -> str:  # type: ignore[override]
        return create_access_token(str(user.id))

    async def read_token(self, token, user_manager) -> Any:  # type: ignore[override]
        if token is None:
            return None
        try:
            data = verify_token(token)
            if data.get("type") != "access":
                return None
            user_id = data.get("sub")
            if not user_id:
                return None
            return await user_manager.get(uuid.UUID(user_id))
        except Exception:
            return None

    async def destroy_token(self, token, user) -> None:  # type: ignore[override]
        # access token is stateless - client discards it
        # refresh token revocation is handled in /auth/logout-all
        pass
