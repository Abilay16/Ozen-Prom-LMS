from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
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
    code = body.code.strip()
    # Check for duplicate code (including inactive disciplines)
    existing = (await db.execute(select(Discipline).where(Discipline.code == code))).scalar_one_or_none()
    if existing:
        if not existing.is_active:
            # Reactivate instead of creating duplicate
            existing.is_active = True
            existing.name = body.name.strip()
            if body.description is not None:
                existing.description = body.description
            await db.flush()
            return existing
        raise HTTPException(status_code=409, detail=f"Дисциплина с кодом «{code}» уже существует")
    disc = Discipline(code=code, name=body.name.strip(), description=body.description)
    db.add(disc)
    await db.flush()
    return disc


@router.patch("/{discipline_id}")
async def update_discipline(discipline_id: UUID, body: DisciplineCreate, db: DB, admin: CurrentAdmin):
    from app.core.exceptions import NotFoundError
    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    disc = result.scalar_one_or_none()
    if not disc:
        raise NotFoundError("Discipline not found")
    # Check code uniqueness against other disciplines
    code = body.code.strip()
    dup = (await db.execute(
        select(Discipline).where(Discipline.code == code, Discipline.id != discipline_id)
    )).scalar_one_or_none()
    if dup:
        raise HTTPException(status_code=409, detail=f"Дисциплина с кодом «{code}» уже существует")
    disc.code = code
    disc.name = body.name.strip()
    if body.description is not None:
        disc.description = body.description
    return disc


@router.delete("/{discipline_id}", status_code=204)
async def delete_discipline(discipline_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Discipline).where(Discipline.id == discipline_id))
    disc = result.scalar_one_or_none()
    if not disc:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Discipline not found")
    disc.is_active = False
