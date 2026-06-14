# ── Imports ───────────────────────────────────────────────────────────────────
import base64
import secrets

import pyotp
from cryptography.fernet import Fernet

from app.core.config import settings
from app.core.security.hashing import hash_password, verify_password

# ── Key helper ────────────────────────────────────────────────────────────────


def _get_fernet() -> Fernet:
    """Helper to load key and return a Fernet instance."""
    key = settings.TOTP_ENCRYPTION_KEY
    if not key:
        if settings.ENVIRONMENT == "production":
            raise ValueError("TOTP_ENCRYPTION_KEY must be set in production")
        # 32-byte development key (base64 encoded)
        key = base64.urlsafe_b64encode(b"dev_totp_secret_key_32_bytes_len").decode()
    return Fernet(key.encode())


# ── Secret Encryption ─────────────────────────────────────────────────────────


def encrypt_secret(secret: str) -> str:
    """Encrypts a plaintext TOTP secret for database storage."""
    fernet = _get_fernet()
    return fernet.encrypt(secret.encode()).decode()


def decrypt_secret(encrypted: str) -> str:
    """Decrypts an encrypted TOTP secret from the database."""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted.encode()).decode()


# ── TOTP Operations ───────────────────────────────────────────────────────────


def generate_totp_secret() -> str:
    """Generates a random base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Generates a provisioning URI for QR code generation."""
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=email,
        issuer_name=settings.APP_NAME,
    )


def verify_totp_code(secret: str, code: str) -> bool:
    """
    Verifies a 6-digit TOTP code.
    Allows a time drift window of +/- 1 interval (30 seconds).
    """
    totp = pyotp.totp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# ── Backup Codes ──────────────────────────────────────────────────────────────


def generate_backup_codes() -> tuple[list[str], list[str]]:
    """
    Generates 8 alphanumeric backup codes.
    Returns: (plain_codes, hashed_codes)
    """
    plain = [secrets.token_hex(4) for _ in range(8)]
    hashed = [hash_password(code) for code in plain]
    return plain, hashed


def verify_and_use_backup_code(
    backup_codes: list[str], code: str
) -> tuple[bool, list[str]]:
    """
    Verifies a backup code.
    If valid, returns (True, updated_backup_codes) with the used code removed.
    """
    for hashed in backup_codes:
        if verify_password(code, hashed):
            updated_codes = [c for c in backup_codes if c != hashed]
            return True, updated_codes
    return False, backup_codes
