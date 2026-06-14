# ── Imports ───────────────────────────────────────────────────────────────────
from typing import Any

from sqladmin import ModelView
from starlette.requests import Request

from app.models.audit_log import AuditLog
from app.models.feature_flag import FeatureFlag
from app.models.invitation import Invitation
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

    # Exclude security credentials and secrets from admin display and forms (handled via form_columns)


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


class FeatureFlagAdmin(ModelView, model=FeatureFlag):
    """Admin view configuration for the FeatureFlag model."""

    column_list = [
        FeatureFlag.id,
        FeatureFlag.name,
        FeatureFlag.description,
        FeatureFlag.enabled_globally,
        FeatureFlag.created_at,
    ]
    column_searchable_list = [FeatureFlag.name, FeatureFlag.description]
    column_filters = [FeatureFlag.enabled_globally]
    form_columns = [
        FeatureFlag.name,
        FeatureFlag.description,
        FeatureFlag.enabled_globally,
        FeatureFlag.enabled_for_plans,
        FeatureFlag.enabled_for_orgs,
    ]

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        """Invalidate cache on creation or update."""
        if hasattr(model, "name") and model.name:
            from app.services.feature_flag_service import (
                invalidate_feature_flag_cache,
            )

            await invalidate_feature_flag_cache(model.name)

    async def on_model_delete(self, model: Any, request: Request) -> None:
        """Invalidate cache on deletion."""
        if hasattr(model, "name") and model.name:
            from app.services.feature_flag_service import (
                invalidate_feature_flag_cache,
            )

            await invalidate_feature_flag_cache(model.name)


class InvitationAdmin(ModelView, model=Invitation):
    """Admin view configuration for the Invitation model."""

    column_list = [
        Invitation.id,
        Invitation.org_id,
        Invitation.email,
        Invitation.role,
        Invitation.invited_by,
        Invitation.expires_at,
        Invitation.accepted_at,
        Invitation.created_at,
    ]
    column_searchable_list = [Invitation.email, Invitation.token]
    column_filters = [Invitation.role, Invitation.accepted_at]
    form_columns = [
        Invitation.org_id,
        Invitation.email,
        Invitation.token,
        Invitation.role,
        Invitation.invited_by,
        Invitation.expires_at,
        Invitation.accepted_at,
    ]
