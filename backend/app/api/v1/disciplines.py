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
