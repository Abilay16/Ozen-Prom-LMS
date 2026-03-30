from uuid import UUID
from typing import Optional
from datetime import date
from fastapi import APIRouter, Query
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, DB
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.attempt import AttemptStatus
from app.models.user import User

router = APIRouter()


@router.get("/stats")
async def get_stats(db: DB, admin: CurrentAdmin):
    from app.models.batch import TrainingBatch
    users_count = (await db.execute(select(func.count()).select_from(User))).scalar()
    batches_count = (await db.execute(select(func.count()).select_from(TrainingBatch))).scalar()
    passed = (await db.execute(
        select(func.count()).select_from(UserCourseAssignment)
        .where(UserCourseAssignment.status == AssignmentStatus.passed)
    )).scalar()
    in_progress = (await db.execute(
        select(func.count()).select_from(UserCourseAssignment)
        .where(UserCourseAssignment.status == AssignmentStatus.in_progress)
    )).scalar()
    failed = (await db.execute(
        select(func.count()).select_from(UserCourseAssignment)
        .where(UserCourseAssignment.status == AssignmentStatus.failed)
    )).scalar()
    total_assignments = (await db.execute(
        select(func.count()).select_from(UserCourseAssignment)
    )).scalar()
    return {
        "users": users_count,
        "batches": batches_count,
        "passed": passed,
        "in_progress": in_progress,
        "failed": failed,
        "total_assignments": total_assignments,
    }


@router.get("")
async def get_progress(
    db: DB,
    admin: CurrentAdmin,
    organization_id: Optional[UUID] = Query(None),
    batch_id: Optional[UUID] = Query(None),
    status: Optional[AssignmentStatus] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(500),
):
    q = (
        select(UserCourseAssignment)
        .options(
            selectinload(UserCourseAssignment.user).selectinload(User.organization),
            selectinload(UserCourseAssignment.course),
            selectinload(UserCourseAssignment.discipline),
            selectinload(UserCourseAssignment.attempts),
        )
        .join(UserCourseAssignment.user)
        .order_by(UserCourseAssignment.assigned_at.desc())
    )
    if batch_id:
        q = q.where(UserCourseAssignment.batch_id == batch_id)
    if status:
        q = q.where(UserCourseAssignment.status == status)
    if organization_id:
        q = q.where(User.organization_id == organization_id)
    if search:
        q = q.where(User.normalized_full_name.ilike(f"%{search.lower()}%"))
    if date_from:
        q = q.where(UserCourseAssignment.assigned_at >= date_from)
    if date_to:
        from datetime import datetime, timezone, timedelta
        dt_to = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
        q = q.where(UserCourseAssignment.assigned_at <= dt_to)
    q = q.limit(limit)
    result = await db.execute(q)
    assignments = result.scalars().all()

    out = []
    for a in assignments:
        u = a.user
        best_score = None
        best_passed = None
        if a.attempts:
            completed = [x for x in a.attempts if x.status == AttemptStatus.completed]
            if completed:
                best = max(completed, key=lambda x: x.score_percent or 0)
                best_score = best.score_percent
                best_passed = best.passed
        out.append({
            "id": str(a.id),
            "status": a.status,
            "assigned_at": a.assigned_at,
            "completed_at": a.completed_at,
            "best_score": best_score,
            "best_passed": best_passed,
            "user": {
                "id": str(u.id),
                "full_name": u.full_name,
                "login": u.login,
                "position_raw": u.position_raw or "",
                "organization_name": u.organization.name if u.organization else "",
            } if u else None,
            "discipline": {"id": str(a.discipline.id), "name": a.discipline.name} if a.discipline else None,
            "course": {"id": str(a.course.id), "name": a.course.name} if a.course else None,
        })
    return out
