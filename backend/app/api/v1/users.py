from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, DB
from app.models.user import User
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError

router = APIRouter()


class UserOut(BaseModel):
    id: UUID
    login: str
    full_name: str
    organization_id: Optional[UUID]
    position_raw: Optional[str]
    is_active: bool
    plain_password: Optional[str] = None

    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.get("/count")
async def count_users(db: DB, admin: CurrentAdmin):
    from sqlalchemy import func
    result = await db.execute(select(func.count()).select_from(User))
    return {"count": result.scalar()}


@router.get("")
async def list_users(
    db: DB,
    admin: CurrentAdmin,
    search: Optional[str] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 50,
):
    q = select(User)
    if search:
        q = q.where(User.normalized_full_name.ilike(f"%{search.lower()}%"))
    if organization_id:
        q = q.where(User.organization_id == organization_id)
    if is_active is not None:
        q = q.where(User.is_active == is_active)
    q = q.offset(skip).limit(limit).order_by(User.full_name)
    result = await db.execute(q)
    return result.scalars().all()


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    position_raw: Optional[str] = None
    new_password: Optional[str] = None


@router.patch("/{user_id}")
async def update_user(user_id: UUID, data: UpdateUserRequest, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    if data.full_name is not None:
        user.full_name = data.full_name
        user.normalized_full_name = data.full_name.strip().lower()
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.position_raw is not None:
        user.position_raw = data.position_raw
    if data.new_password:
        user.password_hash = hash_password(data.new_password)
        user.plain_password = data.new_password
    return user


@router.post("/{user_id}/reset-password")
async def reset_password(user_id: UUID, body: ResetPasswordRequest, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    user.password_hash = hash_password(body.new_password)
    user.plain_password = body.new_password
    return {"message": "Password updated"}
