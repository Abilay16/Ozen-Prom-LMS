from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
from app.core.exceptions import NotFoundError
from app.models.discipline import Discipline
from app.models.course import Course

router = APIRouter()


class DisciplineCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


async def _get(db, discipline_id: UUID) -> Discipline:
    disc = (await db.execute(select(Discipline).where(Discipline.id == discipline_id))).scalar_one_or_none()
    if not disc:
        raise NotFoundError("Дисциплина не найдена")
    return disc


async def _ensure_code_free(db, code: str, exclude_id: UUID | None = None):
    """Код должен быть уникален среди действующих дисциплин; архивные не мешают."""
    q = select(Discipline).where(Discipline.code == code, Discipline.is_active == True)  # noqa: E712
    if exclude_id:
        q = q.where(Discipline.id != exclude_id)
    if (await db.execute(q)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Действующая дисциплина с кодом «{code}» уже есть")


@router.get("")
async def list_disciplines(db: DB, admin: CurrentAdmin, archived: bool = False):
    """Действующие дисциплины, или архивные при archived=true. С числом курсов."""
    course_count = (
        select(func.count()).select_from(Course).where(Course.discipline_id == Discipline.id)
        .correlate(Discipline).scalar_subquery()
    )
    rows = (await db.execute(
        select(Discipline, course_count)
        .where(Discipline.is_active == (not archived))
        .order_by(Discipline.name)
    )).all()
    return [
        {"id": d.id, "code": d.code, "name": d.name, "description": d.description,
         "is_active": d.is_active, "course_count": n}
        for d, n in rows
    ]


@router.post("", status_code=201)
async def create_discipline(body: DisciplineCreate, db: DB, admin: CurrentAdmin):
    code = body.code.strip()
    await _ensure_code_free(db, code)
    disc = Discipline(code=code, name=body.name.strip(), description=body.description)
    db.add(disc)
    await db.flush()
    return disc


@router.patch("/{discipline_id}")
async def update_discipline(discipline_id: UUID, body: DisciplineCreate, db: DB, admin: CurrentAdmin):
    disc = await _get(db, discipline_id)
    code = body.code.strip()
    if disc.is_active:
        await _ensure_code_free(db, code, exclude_id=discipline_id)
    disc.code = code
    disc.name = body.name.strip()
    if body.description is not None:
        disc.description = body.description
    return disc


@router.post("/{discipline_id}/archive")
async def archive_discipline(discipline_id: UUID, db: DB, admin: CurrentAdmin):
    """В архив: больше не предлагается для новых потоков. Курсы, назначения,
    протоколы и удостоверения не трогаются — сотрудники доучиваются."""
    disc = await _get(db, discipline_id)
    disc.is_active = False
    return disc


@router.post("/{discipline_id}/restore")
async def restore_discipline(discipline_id: UUID, db: DB, admin: CurrentAdmin):
    disc = await _get(db, discipline_id)
    if not disc.is_active:
        await _ensure_code_free(db, disc.code, exclude_id=discipline_id)
        disc.is_active = True
    return disc


@router.delete("/{discipline_id}", status_code=204)
async def delete_discipline(discipline_id: UUID, db: DB, admin: CurrentAdmin):
    # Совместимость со старым фронтом: «удаление» всегда было переносом в архив.
    disc = await _get(db, discipline_id)
    disc.is_active = False
