"""Admin-users management: commission eligibility + position title."""
import uuid
import random
import string
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentAdmin, CurrentSuperAdmin, DB
from app.core.exceptions import ConflictError
from app.core.security import hash_password
from app.models.user import AdminUser

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────

class AdminUserOut(BaseModel):
    id: uuid.UUID
    login: str
    full_name: str
    email: Optional[str]
    is_active: bool
    is_superadmin: bool
    is_commission_eligible: bool
    position_title: Optional[str]

    model_config = {"from_attributes": True}


class AdminUserPatch(BaseModel):
    full_name: Optional[str] = None
    position_title: Optional[str] = None
    is_commission_eligible: Optional[bool] = None


class AdminUserCreate(BaseModel):
    full_name: str
    login: Optional[str] = None      # omit to auto-generate
    password: Optional[str] = None   # omit to auto-generate
    email: Optional[str] = None
    position_title: Optional[str] = None
    is_commission_eligible: bool = False


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[AdminUserOut])
async def list_admin_users(
    db: DB,
    _admin: CurrentAdmin,  # all admins can list commission members
):
    result = await db.execute(
        select(AdminUser).where(AdminUser.is_active == True).order_by(AdminUser.full_name)
    )
    return result.scalars().all()


@router.post("", response_model=AdminUserOut, status_code=201)
async def create_admin_user(
    data: AdminUserCreate,
    db: DB,
    admin: CurrentSuperAdmin,
):
    """Only superadmins can create admin accounts."""
    # Determine login
    if data.login:
        existing = await db.execute(select(AdminUser).where(AdminUser.login == data.login))
        if existing.scalar_one_or_none():
            raise ConflictError("Логин уже занят")
        login = data.login
    else:
        from app.utils.transliteration import transliterate_name_to_login
        base = transliterate_name_to_login(data.full_name) or "admin"
        login = base
        for suffix in ('', '2', '3', '4', '5'):
            candidate = base + str(suffix) if suffix else base
            check = await db.execute(select(AdminUser).where(AdminUser.login == candidate))
            if not check.scalar_one_or_none():
                login = candidate
                break
        else:
            login = base + ''.join(random.choices(string.digits, k=4))

    # Determine password
    if data.password:
        plain = data.password
    else:
        letters = random.choices(string.ascii_lowercase, k=3)
        digits = random.choices(string.digits, k=3)
        combo = letters + digits
        random.shuffle(combo)
        plain = ''.join(combo)

    new_admin = AdminUser(
        login=login,
        password_hash=hash_password(plain),
        full_name=data.full_name.strip(),
        email=data.email,
        position_title=data.position_title,
        is_commission_eligible=data.is_commission_eligible,
        is_superadmin=False,
        is_active=True,
    )
    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)
    return new_admin


@router.patch("/{admin_user_id}", response_model=AdminUserOut)
async def patch_admin_user(
    admin_user_id: uuid.UUID,
    data: AdminUserPatch,
    db: DB,
    _admin: CurrentSuperAdmin,
):
    au = await db.get(AdminUser, admin_user_id)
    if not au:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found")

    if data.full_name is not None:
        au.full_name = data.full_name
    if data.position_title is not None:
        au.position_title = data.position_title
    if data.is_commission_eligible is not None:
        au.is_commission_eligible = data.is_commission_eligible

    await db.commit()
    await db.refresh(au)
    return au
