"""Role definitions and helpers for role-based access control (RBAC)."""

ROLE_ADMIN = "admin"
ROLE_USER = "user"
ROLE_VIEWER = "viewer"

VALID_ROLES = (ROLE_ADMIN, ROLE_USER, ROLE_VIEWER)

# Roles a user may self-assign at registration. 'admin' is deliberately
# excluded so a new account can never escalate to admin (privilege escalation).
SELF_REGISTERABLE_ROLES = (ROLE_USER, ROLE_VIEWER)

# Roles allowed to create/update records in the household modules.
WRITE_ROLES = (ROLE_ADMIN, ROLE_USER)
# Roles allowed to delete records.
DELETE_ROLES = (ROLE_ADMIN,)
# Roles allowed to manage servants (create/update/delete).
SERVANT_WRITE_ROLES = (ROLE_ADMIN,)
# Roles allowed to use the AI chat endpoint.
CHAT_ROLES = (ROLE_ADMIN, ROLE_USER)

ROLE_DESCRIPTIONS = {
    ROLE_ADMIN: (
        "Full access to all modules and user management. Can create, update "
        "and delete any record and assign roles."
    ),
    ROLE_USER: (
        "Add and edit expenses, milk and newspaper records; read-only access "
        "to servant salaries; cannot delete records."
    ),
    ROLE_VIEWER: "Read-only access to dashboard and reports.",
}


def is_valid_role(role: str) -> bool:
    return role in VALID_ROLES
