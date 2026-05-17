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
