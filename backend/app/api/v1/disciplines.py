from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.discipline import Discipline

router = APIRouter()


class DisciplineCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


@router.get("")
async def list_disciplines(db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Discipline).where(Discipline.is_active == True).order_by(Discipline.name))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_discipline(body: DisciplineCreate, db: DB, admin: CurrentAdmin):
    disc = Discipline(**body.model_dump())
    db.add(disc)
    await db.flush()
    return disc


@router.delete("/{discipline_id}", status_code=204)
async def delete_discipline(discipline_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    disc = result.scalar_one_or_none()
    if not disc:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Discipline not found")
    disc.is_active = False
