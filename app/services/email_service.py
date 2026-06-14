import json
import logging
import os
from typing import Any

from arq import create_pool
from arq.connections import RedisSettings
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self) -> None:
        # Templates are located in app/templates/emails
        template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates", "emails"
        )
        os.makedirs(template_dir, exist_ok=True)
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def get_arq_pool(self) -> Any:
        return await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))

    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> None:
        """
        Enqueues an email sending job into the arq queue.
        This is called by web routers to avoid blocking requests.
        """
        # Standardize app_name in template context
        context.setdefault("app_name", settings.APP_NAME)

        try:
            pool = await self.get_arq_pool()
            await pool.enqueue_job(
                "send_email_task",
                to_email=to_email,
                subject=subject,
                template_name=template_name,
                context=context,
            )
            logger.info(f"Enqueued email task to {to_email} in Redis queue.")
        except Exception as e:
            logger.error(f"Failed to enqueue email task to {to_email}: {e}")
            # Fallback to direct send in development if arq is disabled or down
            if settings.ENVIRONMENT == "development":
                logger.warning("Falling back to sending email directly in development.")
                await self.send_email_direct(to_email, subject, template_name, context)
            else:
                raise

    async def send_email_direct(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> None:
        """
        Actually sends the email using SMTP or the configured provider.
        This is called by the arq background worker.
        """
        context.setdefault("app_name", settings.APP_NAME)

        # Render HTML template
        try:
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {e}")
            html_content = f"Subject: {subject}\n\nContext: {json.dumps(context)}"

        provider = settings.EMAIL_PROVIDER.lower()
        if provider == "smtp":
            await self._send_smtp(to_email, subject, html_content)
        elif provider in ("sendgrid", "resend"):
            logger.info(f"[MOCK EMAIL API] Sending email via {provider} to {to_email}")
        else:
            logger.warning(
                f"Unknown email provider: {provider}. Logging email instead."
            )
            logger.info(
                f"[EMAIL LOG] To: {to_email} | Subject: {subject} | Body: {html_content[:200]}"
            )

    async def _send_smtp(self, to_email: str, subject: str, html_content: str) -> None:
        import asyncio
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.warning("SMTP credentials not configured. Logging email instead.")
            logger.info(f"[SMTP LOG] To: {to_email} | Subject: {subject}")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(html_content, "html"))

        loop = asyncio.get_running_loop()

        def _send() -> None:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_PORT == 587:
                    server.starttls()
                if settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [to_email], msg.as_string())

        try:
            await loop.run_in_executor(None, _send)
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Failed to send email via SMTP to {to_email}: {e}")
            raise


email_service = EmailService()
