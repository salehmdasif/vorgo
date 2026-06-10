from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy import select

from app.core.database import get_db_context
from app.models.organization import Organization, SubscriptionStatus
from app.models.user import User, UserRole
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


async def trial_expiry_check(ctx: dict) -> None:
    """
    Scheduled task (cron job) to check for trials expiring in 3 days.
    Sends warning emails to organization admins.
    """
    logger.info("Starting trial expiry check...")
    now = datetime.now(timezone.utc)
    target_start = now + timedelta(days=3)
    target_end = now + timedelta(days=4)

    async with get_db_context() as db:
        # Query organizations whose trial expires in 3-4 days
        stmt = select(Organization).where(
            Organization.trial_ends_at >= target_start,
            Organization.trial_ends_at <= target_end,
            Organization.subscription_status == SubscriptionStatus.TRIALING,
        )
        res = await db.execute(stmt)
        orgs = res.scalars().all()

        for org in orgs:
            logger.info(f"Organization {org.name} trial is expiring soon.")
            # Find admins in this org to email
            stmt_users = select(User).where(
                User.org_id == org.id,
                User.role == UserRole.ADMIN,
            )
            res_users = await db.execute(stmt_users)
            admins = res_users.scalars().all()

            # Fallback to all users if no admin exists
            if not admins:
                stmt_all = select(User).where(User.org_id == org.id)
                res_all = await db.execute(stmt_all)
                admins = res_all.scalars().all()

            days_remaining = 3
            if org.trial_ends_at:
                days_remaining = (org.trial_ends_at - now).days

            for admin in admins:
                await email_service.send_email(
                    to_email=admin.email,
                    subject="Your trial is expiring soon",
                    template_name="trial_expiring.html",
                    context={
                        "user_name": admin.email,
                        "org_name": org.name,
                        "days_remaining": days_remaining,
                        "expiry_date": org.trial_ends_at.strftime("%Y-%m-%d") if org.trial_ends_at else "",
                    },
                )
