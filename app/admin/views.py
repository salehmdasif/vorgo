# ── Imports ───────────────────────────────────────────────────────────────────
from sqladmin import ModelView

from app.models.audit_log import AuditLog
from app.models.organization import Organization
from app.models.user import User

# ── Model Views ───────────────────────────────────────────────────────────────


class UserAdmin(ModelView, model=User):
    """Admin view configuration for the User model."""

    column_list = [
        User.id,
        User.email,
        User.role,
        User.is_active,
        User.is_verified,
        User.is_superuser,
        User.created_at,
    ]
    column_searchable_list = [User.email]
    column_filters = [User.role, User.is_active, User.is_verified, User.is_superuser]
    form_columns = [
        User.email,
        User.role,
        User.is_active,
        User.is_verified,
        User.is_superuser,
        User.org_id,
    ]
    column_labels = {User.org_id: "Organization ID"}

    # Exclude security credentials and secrets from admin display and forms
    column_exclude_list = [User.hashed_password, User.totp_secret, User.backup_codes]
    form_excluded_columns = [
        User.hashed_password,
        User.totp_secret,
        User.backup_codes,
    ]


class OrganizationAdmin(ModelView, model=Organization):
    """Admin view configuration for the Organization model."""

    column_list = [
        Organization.id,
        Organization.name,
        Organization.slug,
        Organization.plan,
        Organization.subscription_status,
        Organization.is_active,
        Organization.created_at,
    ]
    column_searchable_list = [Organization.name, Organization.slug]
    column_filters = [
        Organization.plan,
        Organization.subscription_status,
        Organization.is_active,
    ]
    form_columns = [
        Organization.name,
        Organization.slug,
        Organization.plan,
        Organization.subscription_status,
        Organization.is_active,
        Organization.settings,
    ]


class AuditLogAdmin(ModelView, model=AuditLog):
    """Admin view configuration for the AuditLog model."""

    column_list = [
        AuditLog.id,
        AuditLog.org_id,
        AuditLog.user_id,
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
        AuditLog.ip_address,
        AuditLog.created_at,
    ]
    column_searchable_list = [
        AuditLog.action,
        AuditLog.resource_type,
        AuditLog.resource_id,
    ]
    column_filters = [AuditLog.action, AuditLog.resource_type]

    # AuditLog is write-only and immutable - do not allow updates or deletions
    can_create = False
    can_edit = False
    can_delete = False
