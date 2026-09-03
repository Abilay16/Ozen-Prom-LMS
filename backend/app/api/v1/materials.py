from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
from app.models.material import CourseMaterial, MaterialType
from app.core.exceptions import NotFoundError

router = APIRouter()

_OFFICE_EXTENSIONS = {'.ppt', '.pptx', '.doc', '.docx'}


def _convert_to_pdf(file_path: str) -> None:
    """Convert office file to PDF using LibreOffice headless. Runs as a background task after upload."""
    import os, subprocess
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in _OFFICE_EXTENSIONS:
        return
    out_dir = os.path.dirname(file_path)
    try:
        subprocess.run(
            ['libreoffice', '--headless', '--norestore', '--convert-to', 'pdf', '--outdir', out_dir, file_path],
            timeout=120,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            # Use /tmp as HOME so LibreOffice can write its profile in a writable location
            env={**os.environ, 'HOME': '/tmp'},
        )
    except Exception:
        pass  # Conversion failed silently — file still uploaded, just no inline preview


@router.post("/courses/{course_id}", status_code=201)
async def add_material(
    course_id: UUID,
    db: DB,
    admin: CurrentAdmin,
    background_tasks: BackgroundTasks,
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
        max_bytes = settings.MAX_MATERIAL_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(413, f"Файл слишком большой (макс. {settings.MAX_MATERIAL_SIZE_MB} МБ)")
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        # Queue PDF conversion for office files (runs after response is sent)
        if ext in _OFFICE_EXTENSIONS:
            background_tasks.add_task(_convert_to_pdf, file_path)

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
