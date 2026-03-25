from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, DB
from app.models.course import Course
from app.core.exceptions import NotFoundError

router = APIRouter()


class CourseCreate(BaseModel):
    discipline_id: UUID
    name: str
    description: Optional[str] = None
    target_positions: Optional[str] = None
    duration_hours: Optional[int] = None


@router.get("")
async def list_courses(db: DB, admin: CurrentAdmin, discipline_id: Optional[UUID] = None):
    q = select(Course).options(selectinload(Course.discipline))
    if discipline_id:
        q = q.where(Course.discipline_id == discipline_id)
    q = q.order_by(Course.name)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", status_code=201)
async def create_course(body: CourseCreate, db: DB, admin: CurrentAdmin):
    course = Course(**body.model_dump())
    db.add(course)
    await db.flush()
    return course


@router.patch("/{course_id}")
async def update_course(course_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    allowed = {"name", "description", "target_positions", "duration_hours", "is_active"}
    for k, v in data.items():
        if k in allowed:
            setattr(course, k, v)
    return course


@router.delete("/{course_id}", status_code=204)
async def delete_course(course_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundError("Course not found")
    await db.delete(course)


@router.get("/{course_id}/materials")
async def get_course_materials(course_id: UUID, db: DB, admin: CurrentAdmin):
    from app.models.material import CourseMaterial
    result = await db.execute(
        select(CourseMaterial)
        .where(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.sort_order)
    )
    return result.scalars().all()


@router.get("/{course_id}/test")
async def get_course_test(course_id: UUID, db: DB, admin: CurrentAdmin):
    from app.models.test import Test, TestQuestion, TestQuestionOption
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions).selectinload(TestQuestion.options))
        .where(Test.course_id == course_id)
    )
    return result.scalar_one_or_none()


@router.post("/{course_id}/test/import-word", status_code=201)
async def import_test_from_word(
    course_id: UUID,
    db: DB,
    admin: CurrentAdmin,
    file: UploadFile = File(...),
):
    """
    Загрузить тест из .docx файла.
    Если тест уже существует — вопросы заменяются, настройки теста сохраняются.
    Формат: нумерованные вопросы, варианты с буквами, * перед буквой = правильный ответ.
    """
    import uuid as _uuid
    from app.models.test import Test, TestQuestion, TestQuestionOption
    from app.core.docx_parser import parse_docx, validate_parsed

    if not (file.filename or "").endswith((".docx",)):
        raise HTTPException(status_code=400, detail="Только .docx файлы поддерживаются")

    content = await file.read()
    try:
        questions = parse_docx(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка разбора файла: {e}")

    warnings = validate_parsed(questions)
    if not questions:
        raise HTTPException(status_code=422, detail=warnings[0] if warnings else "Файл пуст")

    # Get or create test
    res = await db.execute(select(Test).where(Test.course_id == course_id))
    test = res.scalar_one_or_none()
    if test is None:
        test = Test(
            id=_uuid.uuid4(), course_id=course_id,
            pass_score=70, max_attempts=3,
            time_limit_minutes=0, show_correct_answers=True,
        )
        db.add(test)
        await db.flush()

    # Remove existing questions/options
    existing_ids = (
        await db.execute(select(TestQuestion.id).where(TestQuestion.test_id == test.id))
    ).scalars().all()
    if existing_ids:
        await db.execute(
            delete(TestQuestionOption).where(TestQuestionOption.question_id.in_(existing_ids))
        )
        await db.execute(delete(TestQuestion).where(TestQuestion.test_id == test.id))

    # Insert parsed questions
    for order, pq in enumerate(questions, 1):
        q = TestQuestion(id=_uuid.uuid4(), test_id=test.id, text=pq.text, sort_order=order)
        db.add(q)
        await db.flush()
        for opt_i, po in enumerate(pq.options, 1):
            db.add(TestQuestionOption(
                id=_uuid.uuid4(), question_id=q.id,
                text=po.text, is_correct=po.is_correct, sort_order=opt_i,
            ))
    await db.flush()

    # Reload with relations
    res2 = await db.execute(
        select(Test)
        .options(selectinload(Test.questions).selectinload(TestQuestion.options))
        .where(Test.id == test.id)
    )
    return {"test": res2.scalar_one(), "imported": len(questions), "warnings": warnings}
