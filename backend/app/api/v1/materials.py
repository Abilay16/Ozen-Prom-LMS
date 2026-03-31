from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.material import CourseMaterial, MaterialType
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.post("/courses/{course_id}", status_code=201)
async def add_material(
    course_id: UUID,
    db: DB,
    admin: CurrentAdmin,
    title: str = Form(...),
    material_type: MaterialType = Form(...),
    url: Optional[str] = Form(None),
    sort_order: int = Form(0),
    file: Optional[UploadFile] = File(None),
):
    import os, aiofiles
    from app.core.config import settings

    file_path = None
    file_size = None

    if file:
        import uuid
        mat_dir = os.path.join(settings.STORAGE_LOCAL_PATH, "materials", str(course_id))
        os.makedirs(mat_dir, exist_ok=True)
        # Use UUID filename to avoid Cyrillic/special chars breaking nginx X-Accel-Redirect
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
        safe_name = str(uuid.uuid4()) + ext
        file_path = os.path.join(mat_dir, safe_name)
        content = await file.read()
        file_size = len(content)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

    material = CourseMaterial(
        course_id=course_id,
        title=title,
        material_type=material_type,
        file_path=file_path,
        url=url,
        file_size_bytes=file_size,
        sort_order=sort_order,
    )
    db.add(material)
    await db.flush()
    return material


@router.patch("/{material_id}")
async def update_material(material_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(CourseMaterial).where(CourseMaterial.id == material_id))
    mat = result.scalar_one_or_none()
    if not mat:
        raise NotFoundError("Material not found")
    allowed = {"title", "url", "sort_order"}
    for k, v in data.items():
        if k in allowed:
            setattr(mat, k, v)
    return mat


@router.delete("/{material_id}", status_code=204)
async def delete_material(material_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(CourseMaterial).where(CourseMaterial.id == material_id))
    mat = result.scalar_one_or_none()
    if not mat:
        raise NotFoundError("Material not found")
    await db.delete(mat)
