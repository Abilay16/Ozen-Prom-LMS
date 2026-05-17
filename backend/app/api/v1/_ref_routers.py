from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
from app.models.discipline import Discipline
from app.models.position import Position

router_disciplines = APIRouter()
router_positions = APIRouter()


class DisciplineCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class PositionCreate(BaseModel):
    name: str
    name_kz: Optional[str] = None
    category: Optional[str] = None


@router_disciplines.get("")
async def list_disciplines(db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Discipline).where(Discipline.is_active == True).order_by(Discipline.name))
    return result.scalars().all()


@router_disciplines.post("", status_code=201)
async def create_discipline(body: DisciplineCreate, db: DB, admin: CurrentAdmin):
    disc = Discipline(**body.model_dump())
    db.add(disc)
    await db.flush()
    return disc


@router_positions.get("")
async def list_positions(db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Position).where(Position.is_active == True).order_by(Position.name))
    return result.scalars().all()


@router_positions.post("", status_code=201)
async def create_position(body: PositionCreate, db: DB, admin: CurrentAdmin):
    pos = Position(**body.model_dump())
    db.add(pos)
    await db.flush()
    return pos
