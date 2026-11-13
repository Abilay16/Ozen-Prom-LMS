from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.models.user import User, AdminUser


async def get_current_admin(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError()
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or payload.get("role") != "admin":
        raise UnauthorizedError()
    user_id = payload.get("sub")
    result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise UnauthorizedError()
    return admin


async def get_current_learner(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError()
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or payload.get("role") != "learner":
        raise UnauthorizedError()
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError()
    return user


async def get_current_superadmin(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> AdminUser:
    """Requires a non-commission, non-org-viewer admin (write access).
    Despite the name, this has never actually required is_superadmin=True —
    only "not a pure commission member". Org viewers are always read-only,
    so they're rejected here the same way commission-only members are."""
    if (admin.is_commission_eligible and not admin.is_superadmin) or admin.is_org_viewer:
        raise ForbiddenError("Недостаточно прав. Только для администраторов.")
    return admin


async def get_current_viewer_admin(
    admin: Annotated[AdminUser, Depends(get_current_admin)],
) -> AdminUser:
    """Allows regular/super admins AND org viewers (read-only, scoped to
    their own organization) — but still excludes pure commission members,
    same as get_current_superadmin. Use on read endpoints that org viewers
    need (users, batches, protocols, certificates, progress) together with
    org_scope_id() to apply the actual filter."""
    if admin.is_commission_eligible and not admin.is_superadmin and not admin.is_org_viewer:
        raise ForbiddenError("Недостаточно прав. Только для администраторов.")
    return admin


def org_scope_id(admin: AdminUser):
    """UUID to filter by when the caller is an org viewer, else None (no
    scoping — superadmins and regular admins see everything, as before)."""
    return admin.organization_id if admin.is_org_viewer else None


CurrentAdmin = Annotated[AdminUser, Depends(get_current_admin)]
CurrentSuperAdmin = Annotated[AdminUser, Depends(get_current_superadmin)]
CurrentViewerAdmin = Annotated[AdminUser, Depends(get_current_viewer_admin)]
CurrentLearner = Annotated[User, Depends(get_current_learner)]
DB = Annotated[AsyncSession, Depends(get_db)]
