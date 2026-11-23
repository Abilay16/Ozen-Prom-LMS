from uuid import UUID
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
from app.models.course import Course
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
    import shutil, tempfile
    out_dir = os.path.dirname(file_path)
    # Свой профиль LibreOffice на каждую конвертацию: с общим профилем вторая
    # одновременная конвертация тихо проваливалась (профиль заблокирован).
    profile_dir = tempfile.mkdtemp(prefix="lo_profile_")
    try:
        subprocess.run(
            ['libreoffice', '--headless', '--norestore',
             f'-env:UserInstallation=file://{profile_dir}',
             '--convert-to', 'pdf', '--outdir', out_dir, file_path],
            timeout=180,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, 'HOME': profile_dir},
        )
    except Exception:
        pass  # Conversion failed silently — file still uploaded, just no inline preview
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)


def _remove_material_files(file_path: str | None) -> None:
    """Файл материала и его PDF-копия для просмотра."""
    import os
    if not file_path:
        return
    for path in {file_path, os.path.splitext(file_path)[0] + '.pdf'}:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except OSError:
            pass


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

    if not (await db.execute(select(Course.id).where(Course.id == course_id))).scalar_one_or_none():
        raise NotFoundError("Курс не найден")

    if file:
        import uuid
        mat_dir = os.path.join(settings.STORAGE_LOCAL_PATH, "materials", str(course_id))
        os.makedirs(mat_dir, exist_ok=True)
        # Use UUID filename to avoid Cyrillic/special chars breaking nginx X-Accel-Redirect
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
        safe_name = str(uuid.uuid4()) + ext
        file_path = os.path.join(mat_dir, safe_name)
        # Пишем на диск кусками: раньше файл (видео до 500 МБ) целиком
        # читался в память сервера.
        max_bytes = settings.MAX_MATERIAL_SIZE_MB * 1024 * 1024
        file_size = 0
        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(1024 * 1024):
                    file_size += len(chunk)
                    if file_size > max_bytes:
                        raise HTTPException(413, f"Файл слишком большой (макс. {settings.MAX_MATERIAL_SIZE_MB} МБ)")
                    await f.write(chunk)
        except BaseException:
            _remove_material_files(file_path)
            raise

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
        raise NotFoundError("Материал не найден")
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
        raise NotFoundError("Материал не найден")
    file_path = mat.file_path
    await db.delete(mat)
    await db.flush()
    # Раньше файл оставался на диске навсегда (видео — сотни мегабайт).
    _remove_material_files(file_path)
