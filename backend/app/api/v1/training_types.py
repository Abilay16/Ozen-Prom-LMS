from uuid import UUID
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentAdmin, CurrentSuperAdmin, DB
from app.models.training_type import TrainingType

router = APIRouter()


class TrainingTypeOut(BaseModel):
    id: UUID
    code: str
    name_ru: str
    name_short: str
    validity_years: int
    is_active: bool

    class Config:
        from_attributes = True


class TrainingTypeCreate(BaseModel):
    code: str
    name_ru: str
    name_short: str
    validity_years: int = 1


class TrainingTypeUpdate(BaseModel):
    name_ru: Optional[str] = None
    name_short: Optional[str] = None
    validity_years: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("", response_model=list[TrainingTypeOut])
async def list_training_types(db: DB, admin: CurrentAdmin):  # all admins can read
    result = await db.execute(select(TrainingType).order_by(TrainingType.name_short))
    return result.scalars().all()


@router.post("", response_model=TrainingTypeOut, status_code=201)
async def create_training_type(data: TrainingTypeCreate, db: DB, admin: CurrentSuperAdmin):
    from app.core.exceptions import ConflictError
    existing = await db.execute(select(TrainingType).where(TrainingType.code == data.code))
    if existing.scalar_one_or_none():
        raise ConflictError("Тип с таким кодом уже существует")
    tt = TrainingType(**data.model_dump())
    db.add(tt)
    await db.commit()
    await db.refresh(tt)
    return tt


@router.patch("/{type_id}", response_model=TrainingTypeOut)
async def update_training_type(type_id: UUID, data: TrainingTypeUpdate, db: DB, admin: CurrentSuperAdmin):
    from app.core.exceptions import NotFoundError
    result = await db.execute(select(TrainingType).where(TrainingType.id == type_id))
    tt = result.scalar_one_or_none()
    if not tt:
        raise NotFoundError("Тип обучения не найден")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(tt, field, val)
    await db.commit()
    await db.refresh(tt)
    return tt
