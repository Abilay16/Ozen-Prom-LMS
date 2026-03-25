from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.position import Position

router = APIRouter()


class PositionCreate(BaseModel):
    name: str
    name_kz: Optional[str] = None
    category: Optional[str] = None


@router.get("")
async def list_positions(db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Position).where(Position.is_active == True).order_by(Position.name))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_position(body: PositionCreate, db: DB, admin: CurrentAdmin):
    pos = Position(**body.model_dump())
    db.add(pos)
    await db.flush()
    return pos
