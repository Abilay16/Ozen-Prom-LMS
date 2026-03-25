from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.batch import TrainingBatch, BatchStatus
from app.models.discipline import Discipline
from app.core.exceptions import NotFoundError

router = APIRouter()


class BatchCreate(BaseModel):
    name: str
    discipline_ids: list[UUID] = []
    notes: Optional[str] = None


@router.get("")
async def list_batches(db: DB, admin: CurrentAdmin):
    result = await db.execute(
        select(TrainingBatch).order_by(TrainingBatch.created_at.desc())
    )
    batches = result.scalars().all()
    # Enrich with discipline names
    out = []
    for b in batches:
        disc_names = []
        if b.discipline_ids:
            for did in b.discipline_ids:
                r = await db.execute(select(Discipline).where(Discipline.id == did))
                d = r.scalar_one_or_none()
                if d:
                    disc_names.append(d.name)
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
async def create_batch(body: BatchCreate, db: DB, admin: CurrentAdmin):
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
async def get_batch(batch_id: UUID, db: DB, admin: CurrentAdmin):
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
    disc_names = []
    if batch.discipline_ids:
        for did in batch.discipline_ids:
            r = await db.execute(select(Discipline).where(Discipline.id == did))
            d = r.scalar_one_or_none()
            if d:
                disc_names.append({"id": str(d.id), "name": d.name})
    return {
        "id": batch.id,
        "name": batch.name,
        "status": batch.status,
        "discipline_ids": batch.discipline_ids,
        "disciplines": disc_names,
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


@router.post("/{batch_id}/upload-excel")
async def upload_excel(batch_id: UUID, file: UploadFile = File(...), db: DB = None, admin: CurrentAdmin = None):
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
async def preview_import(batch_id: UUID, db: DB, admin: CurrentAdmin):
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
async def confirm_import(batch_id: UUID, db: DB, admin: CurrentAdmin):
    """Confirm import: create users, assign courses."""
    from app.services.imports.row_processor import ImportRowProcessor

    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")

    processor = ImportRowProcessor(db)
    summary = await processor.process_batch(batch)
    batch.status = BatchStatus.completed
    return summary
