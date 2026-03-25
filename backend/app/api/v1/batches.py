from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.batch import TrainingBatch, BatchStatus
from app.core.exceptions import NotFoundError

router = APIRouter()


class BatchCreate(BaseModel):
    name: str
    organization_id: Optional[UUID] = None
    notes: Optional[str] = None


@router.get("")
async def list_batches(db: DB, admin: CurrentAdmin, organization_id: Optional[UUID] = None):
    q = select(TrainingBatch).order_by(TrainingBatch.created_at.desc())
    if organization_id:
        q = q.where(TrainingBatch.organization_id == organization_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", status_code=201)
async def create_batch(body: BatchCreate, db: DB, admin: CurrentAdmin):
    batch = TrainingBatch(**body.model_dump(), created_by_id=admin.id)
    db.add(batch)
    await db.flush()
    return batch


@router.get("/{batch_id}")
async def get_batch(batch_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(TrainingBatch).where(TrainingBatch.id == batch_id))
    batch = result.scalar_one_or_none()
    if not batch:
        raise NotFoundError("Batch not found")
    return batch


@router.post("/{batch_id}/upload-excel")
async def upload_excel(batch_id: UUID, file: UploadFile = File(...), db: DB = None, admin: CurrentAdmin = None):
    """Upload Excel file for a batch. Returns raw file path."""
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
    return {"file_path": file_path, "message": "File uploaded. Call preview-import next."}


@router.post("/{batch_id}/preview-import")
async def preview_import(batch_id: UUID, db: DB, admin: CurrentAdmin):
    """Parse uploaded Excel and return preview rows without committing."""
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
