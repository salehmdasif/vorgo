"""
ED25519 key pair generate করে .env এ লিখে দেয়।
HS256 না নিয়ে ED25519 নেওয়ার কারণ:
  - asymmetric - private key দিয়ে sign, public key দিয়ে verify
  - public key share করা যায় (microservice), private key server এ থাকে
  - HS256 এ যে secret জানে সে token বানাতেও পারে - এখানে পারবে না

Usage:
    python -m app.scripts.generate_keys
    অথবা: make generate-keys
"""

import base64
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def generate_ed25519_keypair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()

    # Raw format নেওয়া হয়েছে - PEM এর চেয়ে compact, .env এ রাখা সহজ
    # base64 encode করে string হিসেবে রাখা হচ্ছে
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return (
        base64.b64encode(private_bytes).decode(),
        base64.b64encode(public_bytes).decode(),
    )


def update_env_file(private_key: str, public_key: str) -> None:
    env_path = Path(".env")

    if not env_path.exists():
        env_path.write_text("")

    content = env_path.read_text()

    def set_key(content: str, key: str, value: str) -> str:
        # key আগে থেকে থাকলে replace করো, না থাকলে append করো
        pattern = rf"^{key}=.*$"
        replacement = f"{key}={value}"
        if re.search(pattern, content, re.MULTILINE):
            return re.sub(pattern, replacement, content, flags=re.MULTILINE)
        return content + f"\n{replacement}"

    content = set_key(content, "ED25519_PRIVATE_KEY", private_key)
    content = set_key(content, "ED25519_PUBLIC_KEY", public_key)

    env_path.write_text(content)


if __name__ == "__main__":
    private_key, public_key = generate_ed25519_keypair()
    update_env_file(private_key, public_key)
    print("Keys generated and saved to .env")
    # public key print করা safe - এটা share করা যায়
    print(f"Public Key: {public_key}")
