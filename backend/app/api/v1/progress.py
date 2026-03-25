from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, DB
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.attempt import TestAttempt

router = APIRouter()


@router.get("")
async def get_progress(
    db: DB,
    admin: CurrentAdmin,
    organization_id: Optional[UUID] = Query(None),
    batch_id: Optional[UUID] = Query(None),
    status: Optional[AssignmentStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
):
    q = (
        select(UserCourseAssignment)
        .options(
            selectinload(UserCourseAssignment.user),
            selectinload(UserCourseAssignment.course),
            selectinload(UserCourseAssignment.discipline),
        )
        .order_by(UserCourseAssignment.assigned_at.desc())
    )
    if batch_id:
        q = q.where(UserCourseAssignment.batch_id == batch_id)
    if status:
        q = q.where(UserCourseAssignment.status == status)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()
