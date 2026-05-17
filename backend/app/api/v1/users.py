import os
import uuid as _uuid
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, model_validator
from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
from app.models.user import User
from app.core.security import hash_password
from app.core.exceptions import NotFoundError, ConflictError
from app.core.config import settings
from app.services.users.factory import UserFactoryService

router = APIRouter()
public_router = APIRouter()

_PHOTO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_PHOTO_MIME_PREFIXES = ("image/jpeg", "image/png", "image/webp", "image/gif")


class UserOut(BaseModel):
    id: UUID
    login: str
    full_name: str
    organization_id: Optional[UUID]
    position_raw: Optional[str]
    is_active: bool
    plain_password: Optional[str] = None
    photo_path: Optional[str] = None
    photo_url: Optional[str] = None

    @model_validator(mode='after')
    def _set_photo_url(self) -> 'UserOut':
        if self.photo_path and not self.photo_url:
            self.photo_url = f"/api/v1/users/{self.id}/photo"
        return self

    class Config:
        from_attributes = True


class ResetPasswordRequest(BaseModel):
    new_password: str


class CreateUserRequest(BaseModel):
    full_name: str
    position_raw: Optional[str] = None
    organization_name: Optional[str] = None  # free-text; looked up or created
    organization_id: Optional[UUID] = None   # fallback if ID is known
    login: Optional[str] = None       # omit to auto-generate
    password: Optional[str] = None    # omit to auto-generate


@router.post("", response_model=UserOut, status_code=201)
async def create_user(data: CreateUserRequest, db: DB, admin: CurrentAdmin):
    from sqlalchemy import func as sql_func
    from app.models.organization import Organization

    # Resolve organization
    org_id = data.organization_id
    if not org_id and data.organization_name:
        name_clean = data.organization_name.strip()
        result = await db.execute(
            select(Organization).where(
                sql_func.lower(Organization.name) == name_clean.lower()
            )
        )
        org = result.scalar_one_or_none()
        if org:
            org_id = org.id
        else:
            # Create new organization automatically
            new_org = Organization(name=name_clean)
            db.add(new_org)
            await db.flush()
            org_id = new_org.id

    # If custom login provided, check uniqueness
    if data.login:
        existing = await db.execute(select(User).where(User.login == data.login))
        if existing.scalar_one_or_none():
            raise ConflictError("Логин уже занят")

    factory = UserFactoryService(db)
    if data.login:
        plain = data.password or factory.generate_password()
        user = User(
            login=data.login,
            password_hash=hash_password(plain),
            plain_password=plain,
            full_name=data.full_name.strip(),
            normalized_full_name=factory.normalize_full_name(data.full_name),
            organization_id=org_id,
            position_raw=data.position_raw,
        )
        db.add(user)
        await db.flush()
    else:
        user, plain = await factory.create_user(
            full_name=data.full_name,
            organization_id=org_id,
            position_raw=data.position_raw,
        )
        user.plain_password = plain
        if data.password:
            user.password_hash = hash_password(data.password)
            user.plain_password = data.password
            plain = data.password

    await db.commit()
    await db.refresh(user)
    return user


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


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    user.is_active = False


@router.post("/{user_id}/reset-password")
async def reset_password(user_id: UUID, body: ResetPasswordRequest, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    user.password_hash = hash_password(body.new_password)
    user.plain_password = body.new_password
    return {"message": "Password updated"}


# ── Photo upload (admin) ──────────────────────────────────────────────────────

@router.post("/{user_id}/photo", status_code=200)
async def upload_user_photo(user_id: UUID, db: DB, admin: CurrentAdmin, photo: UploadFile = File(...)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")

    content = await photo.read()
    if len(content) > _PHOTO_MAX_BYTES:
        raise HTTPException(413, "Фото слишком большое (макс. 5 МБ)")

    mime = photo.content_type or ""
    if not any(mime.startswith(p) for p in _PHOTO_MIME_PREFIXES):
        raise HTTPException(415, "Недопустимый формат. Разрешены: JPEG, PNG, WEBP, GIF")

    # Store as {user_id}.{ext}
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
    ext = next((ext_map[k] for k in ext_map if mime.startswith(k)), "jpg")

    photo_dir = os.path.join(settings.STORAGE_LOCAL_PATH, "photos")
    os.makedirs(photo_dir, exist_ok=True)
    file_path = os.path.join(photo_dir, f"{user_id}.{ext}")

    # Remove old photo files for this user if extension differs
    for old_ext in ("jpg", "png", "webp", "gif"):
        old_path = os.path.join(photo_dir, f"{user_id}.{old_ext}")
        if old_path != file_path and os.path.exists(old_path):
            os.remove(old_path)

    import aiofiles
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    user.photo_path = file_path
    await db.commit()
    return {"photo_url": f"/api/v1/users/{user_id}/photo"}


# ── Public photo serving ──────────────────────────────────────────────────────

@public_router.get("/{user_id}/photo")
async def get_user_photo(user_id: UUID, db: DB):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.photo_path or not os.path.exists(user.photo_path):
        raise HTTPException(404, "Фото не найдено")

    # Detect content type from extension
    ext = os.path.splitext(user.photo_path)[1].lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".webp": "image/webp", ".gif": "image/gif"}
    media_type = mime_map.get(ext, "image/jpeg")
    return FileResponse(user.photo_path, media_type=media_type)
