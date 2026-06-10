import logging
from typing import Any

from app.services.email_service import email_service

logger = logging.getLogger(__name__)


async def send_email_task(
    ctx: dict,
    to_email: str,
    subject: str,
    template_name: str,
    context: dict[str, Any],
) -> None:
    """
    Background worker task to send emails directly via the configured email provider.
    """
    logger.info(f"Worker executing send_email_task to {to_email}")
    await email_service.send_email_direct(
        to_email=to_email,
        subject=subject,
        template_name=template_name,
        context=context,
    )
