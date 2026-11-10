from typing import List, Set
from fastapi import HTTPException, Depends, status
from core.tenant_security import get_tenant_context

# Baseline RBAC Permissions Matrix
ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {
        "dataset:create", "dataset:read", "dataset:clean", "dataset:profile",
        "dataset:chat", "dataset:export", "dataset:delete", "job:read",
        "report:read", "report:export", "user:manage", "organization:manage", "audit:read"
    },
    "ORG_ADMIN": {
        "dataset:create", "dataset:read", "dataset:clean", "dataset:profile",
        "dataset:chat", "dataset:export", "dataset:delete", "job:read",
        "report:read", "report:export", "user:manage", "audit:read"
    },
    "ANALYST": {
        "dataset:create", "dataset:read", "dataset:clean", "dataset:profile",
        "dataset:chat", "dataset:export", "dataset:delete", "job:read", "report:read", "report:export"
    },
    "VIEWER": {
        "dataset:read", "dataset:profile", "dataset:chat", "report:read", "job:read"
    }
}
# Backward compatibility alias
ROLE_PERMISSIONS["ADMIN"] = ROLE_PERMISSIONS["ORG_ADMIN"]


def has_permission(role: str, permission: str) -> bool:
    """Check if given role possesses the requested permission."""
    role_upper = (role or "").upper()
    allowed_permissions: Set[str] = ROLE_PERMISSIONS.get(role_upper, set())
    return permission in allowed_permissions

def require_permission(permission: str):
    """FastAPI dependency for verifying that authenticated user's role has permission."""
    def dependency(tenant: dict = Depends(get_tenant_context)):
        role = tenant.get("role", "ANALYST")
        if not has_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Role '{role}' does not possess required permission '{permission}'."
            )
        return tenant
    return dependency

def require_role(allowed_roles: List[str]):
    """FastAPI dependency for restricting endpoints to specific roles."""
    allowed_set = {r.upper() for r in allowed_roles}

    def dependency(tenant: dict = Depends(get_tenant_context)):
        user_role = (tenant.get("role") or "").upper()
        if user_role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User role '{user_role}' is not in allowed roles: {allowed_roles}."
            )
        return tenant
    return dependency
