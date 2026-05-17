from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentSuperAdmin as CurrentAdmin, DB
from app.models.test import Test, TestQuestion, TestQuestionOption
from app.core.exceptions import NotFoundError

router = APIRouter()


class TestCreate(BaseModel):
    pass_score: int = 60
    max_attempts: int = 3
    time_limit_minutes: int = 0
    show_correct_answers: bool = False


class OptionIn(BaseModel):
    text: str
    is_correct: bool
    sort_order: int = 0


class QuestionIn(BaseModel):
    text: str
    sort_order: int = 0
    options: List[OptionIn]


@router.post("/courses/{course_id}", status_code=201)
async def create_test(course_id: UUID, body: TestCreate, db: DB, admin: CurrentAdmin):
    test = Test(course_id=course_id, **body.model_dump())
    db.add(test)
    await db.flush()
    return test


@router.patch("/{test_id}")
async def update_test(test_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise NotFoundError("Test not found")
    allowed = {"pass_score", "max_attempts", "time_limit_minutes", "show_correct_answers"}
    for k, v in data.items():
        if k in allowed:
            setattr(test, k, v)
    return test


@router.post("/{test_id}/questions", status_code=201)
async def add_question(test_id: UUID, body: QuestionIn, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Test).where(Test.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise NotFoundError("Test not found")

    question = TestQuestion(test_id=test_id, text=body.text, sort_order=body.sort_order)
    db.add(question)
    await db.flush()

    for opt in body.options:
        option = TestQuestionOption(question_id=question.id, **opt.model_dump())
        db.add(option)

    await db.flush()
    return question


@router.patch("/questions/{question_id}")
async def update_question(question_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(TestQuestion).where(TestQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found")
    if "text" in data:
        q.text = data["text"]
    if "sort_order" in data:
        q.sort_order = data["sort_order"]
    return q


@router.delete("/questions/{question_id}", status_code=204)
async def delete_question(question_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(TestQuestion).where(TestQuestion.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        raise NotFoundError("Question not found")
    await db.delete(q)
