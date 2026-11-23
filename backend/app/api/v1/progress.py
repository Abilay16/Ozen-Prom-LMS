from uuid import UUID
from typing import Optional
from datetime import date
from fastapi import APIRouter, Query, Response
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.api.pagination import paged
from app.api.deps import CurrentSuperAdmin as CurrentAdmin, CurrentViewerAdmin, org_scope_id, DB
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.attempt import TestAttempt, AttemptStatus
from app.models.user import User
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.post("/{assignment_id}/allow-retake", status_code=200)
async def allow_retake(assignment_id: UUID, db: DB, admin: CurrentAdmin):
    """Reset a failed assignment so the learner can retake the test."""
    result = await db.execute(
        select(UserCourseAssignment).where(UserCourseAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Назначение не найдено")

    # Delete all previous attempts so attempt count resets
    await db.execute(
        delete(TestAttempt).where(TestAttempt.assignment_id == assignment_id)
    )

    assignment.status = AssignmentStatus.assigned
    assignment.completed_at = None
    await db.flush()
    return {"ok": True}


@router.get("/stats")
async def get_stats(db: DB, admin: CurrentViewerAdmin):
    from app.models.batch import TrainingBatch
    org_id = org_scope_id(admin)

    users_q = select(func.count()).select_from(User)
    batches_q = select(func.count()).select_from(TrainingBatch)
    assign_q = select(func.count()).select_from(UserCourseAssignment)
    if org_id:
        users_q = users_q.where(User.organization_id == org_id)
        batches_q = batches_q.where(TrainingBatch.organization_id == org_id)
        assign_q = assign_q.join(User, UserCourseAssignment.user_id == User.id).where(User.organization_id == org_id)

    users_count = (await db.execute(users_q)).scalar()
    batches_count = (await db.execute(batches_q)).scalar()
    passed = (await db.execute(
        assign_q.where(UserCourseAssignment.status == AssignmentStatus.passed)
    )).scalar()
    in_progress = (await db.execute(
        assign_q.where(UserCourseAssignment.status == AssignmentStatus.in_progress)
    )).scalar()
    failed = (await db.execute(
        assign_q.where(UserCourseAssignment.status == AssignmentStatus.failed)
    )).scalar()
    total_assignments = (await db.execute(assign_q)).scalar()
    return {
        "users": users_count,
        "batches": batches_count,
        "passed": passed,
        "in_progress": in_progress,
        "failed": failed,
        "total_assignments": total_assignments,
    }


def _filters(admin, organization_id, batch_id, status, search, date_from, date_to) -> list:
    """Условия на назначение (UserCourseAssignment) и его сотрудника (User) —
    общие для списка по курсам и списка по сотрудникам."""
    from datetime import datetime, timezone
    conds = []
    if batch_id:
        conds.append(UserCourseAssignment.batch_id == batch_id)
    if status:
        conds.append(UserCourseAssignment.status == status)
    org_id = org_scope_id(admin)
    if org_id:
        conds.append(User.organization_id == org_id)
    elif organization_id:
        conds.append(User.organization_id == organization_id)
    if search and search.strip():
        conds.append(User.normalized_full_name.ilike(f"%{search.strip().lower()}%"))
    if date_from:
        conds.append(UserCourseAssignment.assigned_at >= date_from)
    if date_to:
        conds.append(UserCourseAssignment.assigned_at <= datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc))
    return conds


def _best(a: UserCourseAssignment) -> tuple:
    completed = [x for x in (a.attempts or []) if x.status == AttemptStatus.completed]
    if not completed:
        return None, None
    best = max(completed, key=lambda x: x.score_percent or 0)
    return best.score_percent, best.passed


def _assignment_out(a: UserCourseAssignment) -> dict:
    best_score, best_passed = _best(a)
    return {
        "id": str(a.id),
        "status": a.status,
        "assigned_at": a.assigned_at,
        "completed_at": a.completed_at,
        "best_score": best_score,
        "best_passed": best_passed,
        "attempts_used": sum(1 for x in (a.attempts or []) if x.status == AttemptStatus.completed),
        "discipline": {"id": str(a.discipline.id), "name": a.discipline.name} if a.discipline else None,
        "course": {"id": str(a.course.id), "name": a.course.name} if a.course else None,
    }


def _user_out(u: User) -> dict:
    return {
        "id": str(u.id),
        "full_name": u.full_name,
        "login": u.login,
        "position_raw": u.position_raw or "",
        "organization_name": u.organization.name if u.organization else "",
    }


@router.get("/by-user")
async def get_progress_by_user(
    db: DB,
    admin: CurrentViewerAdmin,
    organization_id: Optional[UUID] = Query(None),
    batch_id: Optional[UUID] = Query(None),
    status: Optional[AssignmentStatus] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    response: Response = None,
    skip: int = 0,
    limit: int = Query(50),
):
    """Прогресс по сотрудникам: одна запись на человека со всеми его
    обучениями (раньше один человек повторялся строкой на каждый курс).
    Постранично — по сотрудникам, чтобы обучения одного человека не
    разъезжались по разным страницам."""
    conds = _filters(admin, organization_id, batch_id, status, search, date_from, date_to)

    users_q = (
        select(User.id, User.full_name)
        .join(UserCourseAssignment, UserCourseAssignment.user_id == User.id)
        .where(*conds)
        .group_by(User.id, User.full_name)
        .order_by(User.full_name, User.id)
    )
    rows = await paged(db, users_q, response, skip, limit, scalars=False)
    user_ids = [r.id for r in rows]
    if not user_ids:
        return []

    users = {
        u.id: u for u in (await db.execute(
            select(User).options(selectinload(User.organization)).where(User.id.in_(user_ids))
        )).scalars().all()
    }
    assignments = (await db.execute(
        select(UserCourseAssignment)
        .join(User, UserCourseAssignment.user_id == User.id)
        .options(
            selectinload(UserCourseAssignment.course),
            selectinload(UserCourseAssignment.discipline),
            selectinload(UserCourseAssignment.attempts),
        )
        .where(UserCourseAssignment.user_id.in_(user_ids), *conds)
        .order_by(UserCourseAssignment.assigned_at.desc())
    )).scalars().all()

    by_user: dict = {uid: [] for uid in user_ids}
    for a in assignments:
        by_user[a.user_id].append(_assignment_out(a))

    out = []
    for uid in user_ids:
        items = by_user[uid]
        counts = {s.value: 0 for s in AssignmentStatus}
        for a in items:
            counts[a["status"].value if hasattr(a["status"], "value") else a["status"]] += 1
        out.append({
            "user": _user_out(users[uid]),
            "assignments": items,
            "summary": {"total": len(items), **counts},
        })
    return out


@router.get("")
async def get_progress(
    db: DB,
    admin: CurrentViewerAdmin,
    organization_id: Optional[UUID] = Query(None),
    batch_id: Optional[UUID] = Query(None),
    status: Optional[AssignmentStatus] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    response: Response = None,
    skip: int = 0,
    limit: int = Query(100),
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
        .where(*_filters(admin, organization_id, batch_id, status, search, date_from, date_to))
        .order_by(UserCourseAssignment.assigned_at.desc())
    )
    assignments = await paged(db, q, response, skip, limit)
    return [{**_assignment_out(a), "user": _user_out(a.user) if a.user else None} for a in assignments]
