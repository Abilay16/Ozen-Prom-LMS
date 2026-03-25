from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, DB
from app.models.course import Course
from app.core.exceptions import NotFoundError

router = APIRouter()


class CourseCreate(BaseModel):
    discipline_id: UUID
    name: str
    description: Optional[str] = None
    target_positions: Optional[str] = None
    duration_hours: Optional[int] = None


@router.get("")
async def list_courses(db: DB, admin: CurrentAdmin, discipline_id: Optional[UUID] = None):
    q = select(Course).options(selectinload(Course.discipline))
    if discipline_id:
        q = q.where(Course.discipline_id == discipline_id)
    q = q.order_by(Course.name)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", status_code=201)
async def create_course(body: CourseCreate, db: DB, admin: CurrentAdmin):
    course = Course(**body.model_dump())
    db.add(course)
    await db.flush()
    return course


@router.patch("/{course_id}")
async def update_course(course_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    allowed = {"name", "description", "target_positions", "duration_hours", "is_active"}
    for k, v in data.items():
        if k in allowed:
            setattr(course, k, v)
    return course


@router.delete("/{course_id}", status_code=204)
async def delete_course(course_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    await db.delete(course)


@router.get("/{course_id}/materials")
async def get_course_materials(course_id: UUID, db: DB, admin: CurrentAdmin):
    from app.models.material import CourseMaterial
    result = await db.execute(
        select(CourseMaterial)
        .where(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.sort_order)
    )
    return result.scalars().all()


@router.get("/{course_id}/test")
async def get_course_test(course_id: UUID, db: DB, admin: CurrentAdmin):
    from app.models.test import Test
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions))
        .where(Test.course_id == course_id)
    )
    return result.scalar_one_or_none()
