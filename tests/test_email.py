import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.email_service import email_service
from app.tasks.email_tasks import send_email_task


@pytest.mark.asyncio
async def test_email_rendering() -> None:
    # Verify Jinja environment can render templates
    context = {"app_name": "Vorgo Test", "user_name": "test@user.com"}
    template = email_service.jinja_env.get_template("welcome.html")
    html = template.render(**context)
    assert "Welcome" in html
    assert "test@user.com" in html


@pytest.mark.asyncio
async def test_email_enqueue() -> None:
    # Mock arq redis pool
    mock_pool = AsyncMock()

    with patch.object(email_service, "get_arq_pool", return_value=mock_pool):
        await email_service.send_email(
            to_email="test@user.com",
            subject="Test Welcome",
            template_name="welcome.html",
            context={"user_name": "test@user.com"},
        )

        mock_pool.enqueue_job.assert_called_once_with(
            "send_email_task",
            to_email="test@user.com",
            subject="Test Welcome",
            template_name="welcome.html",
            context={"user_name": "test@user.com", "app_name": "Vorgo"},
        )


@pytest.mark.asyncio
async def test_send_email_direct_smtp() -> None:
    # Mock SMTP object
    mock_smtp_instance = MagicMock()

    with patch("smtplib.SMTP") as mock_smtp_class, patch(
        "app.core.config.settings.EMAIL_PROVIDER", "smtp"
    ), patch("app.core.config.settings.SMTP_HOST", "smtp.test.com"), patch(
        "app.core.config.settings.SMTP_USER", "test@test.com"
    ), patch(
        "app.core.config.settings.SMTP_PASSWORD", "secret"
    ):
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance

        await email_service.send_email_direct(
            to_email="recipient@test.com",
            subject="Direct test",
            template_name="welcome.html",
            context={"user_name": "recipient"},
        )

        # Verify SMTP server was called to sendmail
        mock_smtp_instance.sendmail.assert_called_once()
        args, kwargs = mock_smtp_instance.sendmail.call_args
        assert args[0] == "test@test.com"
        assert args[1] == ["recipient@test.com"]
