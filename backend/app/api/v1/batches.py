from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File
from sqlalchemy import select

from app.api.deps import CurrentAdmin, CurrentSuperAdmin, DB
from app.models.batch import TrainingBatch, BatchStatus
from app.models.discipline import Discipline
from app.core.exceptions import NotFoundError

router = APIRouter()


class BatchCreate(BaseModel):
    name: str
    discipline_ids: list[UUID] = []
    notes: Optional[str] = None


@router.get("")
async def list_batches(db: DB, admin: CurrentAdmin):  # all admins can read
    result = await db.execute(
        select(TrainingBatch).order_by(TrainingBatch.created_at.desc())
    )
    batches = result.scalars().all()

    # Collect all discipline IDs in one query
    all_disc_ids = set()
    for b in batches:
        if b.discipline_ids:
            for did in b.discipline_ids:
                all_disc_ids.add(did)

    disc_map: dict = {}
    if all_disc_ids:
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID
        disc_result = await db.execute(
            select(Discipline).where(Discipline.id.in_(list(all_disc_ids)))
        )
        for d in disc_result.scalars().all():
            disc_map[str(d.id)] = d.name

    out = []
    for b in batches:
        disc_names = [disc_map[str(did)] for did in (b.discipline_ids or []) if str(did) in disc_map]
        out.append({
            "id": b.id,
            "name": b.name,
            "status": b.status,
            "discipline_ids": b.discipline_ids,
            "discipline_names": disc_names,
            "created_at": b.created_at,
            "notes": b.notes,
        })
    return out


@router.post("", status_code=201)
async def create_batch(body: BatchCreate, db: DB, admin: CurrentSuperAdmin):
    batch = TrainingBatch(
        name=body.name,
        notes=body.notes,
        discipline_ids=[str(did) for did in body.discipline_ids],
        created_by_id=admin.id,
    )
    db.add(batch)
    await db.flush()
    return batch


@router.get("/{batch_id}")
async def get_batch(batch_id: UUID, db: DB, admin: CurrentAdmin):  # all admins can read
    from app.models.import_row import ImportRow
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(TrainingBatch).where(TrainingBatch.id == batch_id)
    )
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")
    # Count import rows
    rows_result = await db.execute(
        select(ImportRow).where(ImportRow.batch_id == batch_id)
    )
    rows = rows_result.scalars().all()
    disc_names_detail = []
    if batch.discipline_ids:
        disc_result = await db.execute(
            select(Discipline).where(Discipline.id.in_(batch.discipline_ids))
        )
        disc_names_detail = [
            {"id": str(d.id), "name": d.name}
            for d in disc_result.scalars().all()
        ]
    return {
        "id": batch.id,
        "name": batch.name,
        "status": batch.status,
        "discipline_ids": batch.discipline_ids,
        "disciplines": disc_names_detail,
        "notes": batch.notes,
        "created_at": batch.created_at,
        "excel_file_path": batch.excel_file_path,
        "row_summary": {
            "total": len(rows),
            "ok": sum(1 for r in rows if str(r.status) in ("ok", "ImportRowStatus.ok")),
            "duplicate": sum(1 for r in rows if "duplicate" in str(r.status)),
            "error": sum(1 for r in rows if "error" in str(r.status)),
            "manual_review": sum(1 for r in rows if "manual_review" in str(r.status)),
        },
    }


@router.delete("/{batch_id}", status_code=204)
async def delete_batch(batch_id: UUID, db: DB, admin: CurrentSuperAdmin, deactivate_users: bool = False):
    """Delete a batch. If deactivate_users=true, also deactivate all users in this batch."""
    from app.models.user import User
    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")
    if deactivate_users:
        users_result = await db.execute(select(User).where(User.batch_id == batch_id))
        for u in users_result.scalars().all():
            u.is_active = False
    await db.delete(batch)


@router.post("/{batch_id}/upload-excel")
async def upload_excel(batch_id: UUID, db: DB, admin: CurrentSuperAdmin, file: UploadFile = File(...)):
    import os, aiofiles
    from app.core.config import settings

    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")

    upload_dir = os.path.join(settings.STORAGE_LOCAL_PATH, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"batch_{batch_id}_{file.filename}")

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    batch.excel_file_path = file_path
    batch.status = BatchStatus.processing
    return {"ok": True}


@router.post("/{batch_id}/preview-import")
async def preview_import(batch_id: UUID, db: DB, admin: CurrentSuperAdmin):
    from app.services.imports.parser import ImportParserService

    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")
    if not batch.excel_file_path:
        raise NotFoundError("No Excel file uploaded for this batch")

    service = ImportParserService()
    preview = service.parse_preview(batch.excel_file_path)
    return preview


@router.post("/{batch_id}/confirm-import")
async def confirm_import(batch_id: UUID, db: DB, admin: CurrentSuperAdmin):
    """Confirm import: create users, assign courses."""
    from app.services.imports.row_processor import ImportRowProcessor

    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")

    processor = ImportRowProcessor(db)
    summary = await processor.process_batch(batch)
    if "error" not in summary:
        batch.status = BatchStatus.completed
    return summary


class ManualUserAdd(BaseModel):
    full_name: str
    position: str = ""
    organization: str = ""


@router.post("/{batch_id}/add-user", status_code=201)
async def add_user_manually(batch_id: UUID, body: ManualUserAdd, db: DB, admin: CurrentSuperAdmin):
    """Manually add a single user to a batch and assign courses."""
    from fastapi import HTTPException
    from app.services.users.factory import UserFactoryService
    from app.services.positions.normalizer import normalize_position, find_course_for_position
    from app.models.organization import Organization
    from app.models.user import User
    from app.models.assignment import UserCourseAssignment, AssignmentStatus
    from app.models.course import Course

    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")

    full_name = body.full_name.strip()
    position_raw = body.position.strip()
    org_name = body.organization.strip()

    if not full_name:
        raise HTTPException(status_code=422, detail="ФИО не может быть пустым")

    # Get or create organization
    org = None
    if org_name:
        res = await db.execute(select(Organization))
        for o in res.scalars().all():
            if o.name.strip().lower() == org_name.lower():
                org = o
                break
        if not org:
            org = Organization(name=org_name, is_active=True)
            db.add(org)
            await db.flush()
    org_id = org.id if org else None

    norm_name = UserFactoryService.normalize_full_name(full_name)
    norm_position = normalize_position(position_raw)

    # Duplicate check
    dup_q = select(User).where(User.normalized_full_name == norm_name)
    if org_id:
        dup_q = dup_q.where(User.organization_id == org_id)
    existing = (await db.execute(dup_q)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Пользователь «{full_name}» уже существует в этой организации")

    # Create user
    user_factory = UserFactoryService(db)
    user, plain_password = await user_factory.create_user(
        full_name=full_name,
        organization_id=org_id,
        position_raw=position_raw,
        batch_id=batch.id,
    )

    # Assign courses for each discipline in the batch
    batch_disciplines: list[Discipline] = []
    for did in (batch.discipline_ids or []):
        r = await db.execute(select(Discipline).where(Discipline.id == did))
        d = r.scalar_one_or_none()
        if d:
            batch_disciplines.append(d)

    assigned_courses = []
    for disc in batch_disciplines:
        course = await find_course_for_position(db, disc.id, norm_position)
        if course:
            db.add(UserCourseAssignment(
                user_id=user.id, course_id=course.id,
                discipline_id=disc.id, batch_id=batch.id,
                status=AssignmentStatus.assigned,
            ))
            assigned_courses.append(f"{disc.name}: {course.name}")

    await db.flush()
    return {
        "user_id": str(user.id),
        "full_name": full_name,
        "login": user.login,
        "password": plain_password,
        "organization": org_name,
        "position": position_raw,
        "courses": ", ".join(assigned_courses) or "—",
    }


@router.post("/{batch_id}/users/{user_id}/rematch-courses", status_code=200)
async def rematch_user_courses(batch_id: UUID, user_id: UUID, db: DB, admin: CurrentSuperAdmin):
    """Re-run course matching for one batch member against the batch's current
    disciplines/courses. Useful after an admin fixes a course's target_positions
    (or adds a new course) to cover a position that didn't match at import/add
    time — without this, such a user would be stuck with zero course
    assignments forever and could never appear in a protocol."""
    from app.services.positions.normalizer import normalize_position, find_course_for_position
    from app.models.user import User
    from app.models.assignment import UserCourseAssignment, AssignmentStatus

    batch = (await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))).scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")

    norm_position = normalize_position(user.position_raw or "")

    existing_res = await db.execute(
        select(UserCourseAssignment).where(UserCourseAssignment.user_id == user_id)
    )
    covered_discipline_ids = {a.discipline_id for a in existing_res.scalars().all()}

    assigned_courses = []
    for did in (batch.discipline_ids or []):
        if did in covered_discipline_ids:
            continue
        disc = (await db.execute(select(Discipline).where(Discipline.id == did))).scalar_one_or_none()
        if not disc:
            continue
        course = await find_course_for_position(db, disc.id, norm_position)
        if course:
            db.add(UserCourseAssignment(
                user_id=user.id, course_id=course.id,
                discipline_id=disc.id, batch_id=batch.id,
                status=AssignmentStatus.assigned,
            ))
            assigned_courses.append(f"{disc.name}: {course.name}")

    await db.flush()
    return {"courses": ", ".join(assigned_courses) or "—"}
