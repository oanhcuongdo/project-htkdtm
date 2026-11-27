"""Role-Based Access Control (RBAC) roles, permissions, and lookup helpers.

Mapping between project outline roles and canonical RBAC enum values:
- Admin -> ADMIN
- Manager -> MANAGER
- Pricing Specialist -> PRICING_ANALYST
- Operator -> INVENTORY_STAFF
- Analyst -> VIEWER

Keep permission keys and role names synchronized with `frontend/src/lib/rbac.ts`.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    """Canonical RBAC roles shared between backend and frontend."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    PRICING_ANALYST = "PRICING_ANALYST"
    INVENTORY_STAFF = "INVENTORY_STAFF"
    VIEWER = "VIEWER"


class Permission(StrEnum):
    """Granular permission keys enforced by API dependencies."""

    PRODUCT_READ = "product.read"
    PRODUCT_WRITE = "product.write"
    INVENTORY_READ = "inventory.read"
    INVENTORY_WRITE = "inventory.write"
    CHANNEL_READ = "channel.read"
    CHANNEL_WRITE = "channel.write"
    COMPETITOR_READ = "competitor.read"
    COMPETITOR_WRITE = "competitor.write"
    PRICING_READ = "pricing.read"
    PRICING_RUN = "pricing.run"
    PRICING_APPROVE = "pricing.approve"
    RULE_READ = "rule.read"
    RULE_WRITE = "rule.write"
    EXECUTION_READ = "execution.read"
    EXECUTION_RETRY = "execution.retry"
    BI_READ = "bi.read"
    SETTINGS_READ = "settings.read"
    SETTINGS_WRITE = "settings.write"
    AUDIT_READ = "audit.read"
    USER_MANAGE = "user.manage"


_READ_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        Permission.PRODUCT_READ,
        Permission.INVENTORY_READ,
        Permission.CHANNEL_READ,
        Permission.COMPETITOR_READ,
        Permission.PRICING_READ,
        Permission.RULE_READ,
        Permission.EXECUTION_READ,
        Permission.BI_READ,
    }
)

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.ADMIN: frozenset(Permission),
    Role.MANAGER: (
        _READ_PERMISSIONS
        | frozenset(
            {
                Permission.SETTINGS_READ,
                Permission.AUDIT_READ,
                Permission.PRICING_RUN,
                Permission.PRICING_APPROVE,
                Permission.RULE_WRITE,
                Permission.EXECUTION_RETRY,
            }
        )
    ),
    Role.PRICING_ANALYST: frozenset(
        {
            Permission.PRODUCT_READ,
            Permission.INVENTORY_READ,
            Permission.CHANNEL_READ,
            Permission.COMPETITOR_READ,
            Permission.COMPETITOR_WRITE,
            Permission.PRICING_READ,
            Permission.PRICING_RUN,
            Permission.RULE_READ,
            Permission.RULE_WRITE,
            Permission.EXECUTION_READ,
            Permission.BI_READ,
        }
    ),
    Role.INVENTORY_STAFF: frozenset(
        {
            Permission.PRODUCT_READ,
            Permission.PRODUCT_WRITE,
            Permission.INVENTORY_READ,
            Permission.INVENTORY_WRITE,
            Permission.CHANNEL_READ,
            Permission.CHANNEL_WRITE,
            Permission.COMPETITOR_READ,
            Permission.BI_READ,
        }
    ),
    Role.VIEWER: _READ_PERMISSIONS,
}


def permissions_for_role(role: Role | str | None) -> frozenset[Permission]:
    """Return the permission set granted to a role, or empty set if unknown."""
    if role is None:
        return frozenset()
    try:
        resolved = role if isinstance(role, Role) else Role(role)
    except ValueError:
        return frozenset()
    return ROLE_PERMISSIONS.get(resolved, frozenset())


def has_permission(role: Role | str | None, permission: Permission | str) -> bool:
    """Return True when the given role includes the requested permission."""
    try:
        resolved_perm = (
            permission if isinstance(permission, Permission) else Permission(permission)
        )
    except ValueError:
        return False
    return resolved_perm in permissions_for_role(role)
