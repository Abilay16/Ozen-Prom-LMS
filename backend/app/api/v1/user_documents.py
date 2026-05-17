"""
API endpoints for user-uploaded documents (learner-side).

Learners can upload their own certificates/documents (PDF, images, Office files)
so that all documents are available in one place in their personal cabinet.

Routes (mounted at /learner/documents):
  GET    /            — list own documents
  POST   /            — upload new document
  GET    /{id}/download — download/view file
  DELETE /{id}        — delete document
"""
import os
import uuid
from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import CurrentLearner, DB
from app.core.config import settings
from app.models.user_document import UserDocument

router = APIRouter()

# Allowed MIME types / extensions for uploaded documents
_ALLOWED_MIME_PREFIXES = (
    "application/pdf",
    "image/",
    "application/msword",
    "application/vnd.openxmlformats",
    "application/vnd.ms-",
)
_MAX_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


class DocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    original_filename: str
    mime_type: Optional[str]
    file_size: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# ── List ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[DocumentOut])
async def list_my_documents(learner: CurrentLearner, db: DB):
    result = await db.execute(
        select(UserDocument)
        .where(UserDocument.user_id == learner.id)
        .order_by(UserDocument.uploaded_at.desc())
    )
    return result.scalars().all()


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    learner: CurrentLearner,
    db: DB,
    title: str = Form(...),
    file: UploadFile = File(...),
):
    content = await file.read()

    if len(content) > _MAX_SIZE_BYTES:
        raise HTTPException(413, "Файл слишком большой (макс. 20 МБ)")

    mime = file.content_type or ""
    if not any(mime.startswith(p) for p in _ALLOWED_MIME_PREFIXES):
        raise HTTPException(415, "Недопустимый тип файла. Разрешены: PDF, изображения, Word, Excel")

    # Sanitize title
    title = title.strip()[:255] or file.filename or "Документ"

    # Save file
    doc_dir = os.path.join(settings.STORAGE_LOCAL_PATH, "user_docs", str(learner.id))
    os.makedirs(doc_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(doc_dir, stored_name)

    import aiofiles
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    doc = UserDocument(
        user_id=learner.id,
        title=title,
        original_filename=file.filename or stored_name,
        file_path=file_path,
        mime_type=mime or None,
        file_size=len(content),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


# ── Download ──────────────────────────────────────────────────────────────────

@router.get("/{doc_id}/download")
async def download_document(doc_id: uuid.UUID, learner: CurrentLearner, db: DB):
    result = await db.execute(
        select(UserDocument).where(
            UserDocument.id == doc_id,
            UserDocument.user_id == learner.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Документ не найден")
    if not os.path.exists(doc.file_path):
        raise HTTPException(404, "Файл не найден на сервере")

    return FileResponse(
        doc.file_path,
        media_type=doc.mime_type or "application/octet-stream",
        filename=doc.original_filename,
    )


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, learner: CurrentLearner, db: DB):
    result = await db.execute(
        select(UserDocument).where(
            UserDocument.id == doc_id,
            UserDocument.user_id == learner.id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Документ не найден")

    # Remove file from disk
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except OSError:
        pass  # log in production; don't fail the DB delete

    await db.delete(doc)
    await db.commit()
