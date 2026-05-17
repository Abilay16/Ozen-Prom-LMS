from uuid import UUID
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel

from fastapi import APIRouter
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentLearner, DB
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.course import Course
from app.models.material import CourseMaterial
from app.models.test import Test, TestQuestion
from app.core.exceptions import NotFoundError, ForbiddenError

router = APIRouter()


@router.get("/me")
async def get_me(learner: CurrentLearner, db: DB):
    # Load org and position for the print card
    from sqlalchemy import select as _select
    from app.models.user import User
    user_q = await db.execute(
        _select(User)
        .options(selectinload(User.organization), selectinload(User.position))
        .where(User.id == learner.id)
    )
    user = user_q.scalar_one_or_none() or learner
    return {
        "id": str(learner.id),
        "login": learner.login,
        "full_name": learner.full_name,
        "verify_token": str(learner.verify_token) if learner.verify_token else None,
        "organization_name": user.organization.name if user.organization else None,
        "position": user.position_raw or (user.position.name if user.position else None),
    }


@router.get("/me/courses")
async def my_courses(db: DB, learner: CurrentLearner):
    result = await db.execute(
        select(UserCourseAssignment)
        .options(
            selectinload(UserCourseAssignment.course),
            selectinload(UserCourseAssignment.discipline),
            selectinload(UserCourseAssignment.attempts),
        )
        .where(UserCourseAssignment.user_id == learner.id)
        .order_by(UserCourseAssignment.assigned_at.desc())
    )
    return result.scalars().all()


@router.get("/me/courses/{assignment_id}")
async def get_course_detail(assignment_id: UUID, db: DB, learner: CurrentLearner):
    result = await db.execute(
        select(UserCourseAssignment)
        .options(
            selectinload(UserCourseAssignment.course).selectinload(Course.materials),
            selectinload(UserCourseAssignment.course).selectinload(Course.test),
            selectinload(UserCourseAssignment.discipline),
            selectinload(UserCourseAssignment.attempts),
        )
        .where(
            UserCourseAssignment.id == assignment_id,
            UserCourseAssignment.user_id == learner.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment not found")
    return assignment


@router.post("/me/courses/{assignment_id}/start-test")
async def start_test(assignment_id: UUID, db: DB, learner: CurrentLearner):
    result = await db.execute(
        select(UserCourseAssignment)
        .options(selectinload(UserCourseAssignment.course).selectinload(Course.test))
        .where(
            UserCourseAssignment.id == assignment_id,
            UserCourseAssignment.user_id == learner.id,
        )
    )
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise NotFoundError("Assignment not found")
    if assignment.status == AssignmentStatus.passed:
        raise ForbiddenError("Course already passed")

    test = assignment.course.test
    if not test:
        raise NotFoundError("No test for this course")

    # Count attempts
    att_result = await db.execute(
        select(TestAttempt).where(
            TestAttempt.assignment_id == assignment_id,
            TestAttempt.user_id == learner.id,
        )
    )
    attempts = att_result.scalars().all()
    if test.max_attempts > 0 and len(attempts) >= test.max_attempts:
        raise ForbiddenError("Maximum attempts reached")

    attempt = TestAttempt(
        user_id=learner.id,
        assignment_id=assignment_id,
        test_id=test.id,
        attempt_number=len(attempts) + 1,
    )
    db.add(attempt)
    assignment.status = AssignmentStatus.in_progress
    await db.flush()

    # Return questions WITHOUT correct answers
    t_result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions).selectinload(TestQuestion.options))
        .where(Test.id == test.id)
    )
    loaded_test = t_result.scalar_one()
    return {
        "attempt_id": str(attempt.id),
        "test_id": str(loaded_test.id),
        "time_limit_minutes": loaded_test.time_limit_minutes,
        "total_questions": len(loaded_test.questions),
        "questions": [
            {
                "id": str(q.id),
                "text": q.text,
                "options": [{"id": str(o.id), "text": o.text} for o in q.options],
            }
            for q in loaded_test.questions
        ],
    }


class SubmitAnswers(BaseModel):
    answers: List[dict]  # [{"question_id": "...", "option_id": "..."}]


@router.post("/me/tests/{attempt_id}/submit")
async def submit_test(attempt_id: UUID, body: SubmitAnswers, db: DB, learner: CurrentLearner):
    from app.services.tests.engine import TestEngineService

    result = await db.execute(
        select(TestAttempt)
        .options(selectinload(TestAttempt.assignment))
        .where(TestAttempt.id == attempt_id, TestAttempt.user_id == learner.id)
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise NotFoundError("Attempt not found")
    if attempt.status != AttemptStatus.in_progress:
        raise ForbiddenError("Attempt already submitted")

    engine = TestEngineService(db)
    result_data = await engine.calculate_result(attempt, body.answers)
    return result_data


@router.get("/me/tests/{attempt_id}/result")
async def get_result(attempt_id: UUID, db: DB, learner: CurrentLearner):
    result = await db.execute(
        select(TestAttempt)
        .where(TestAttempt.id == attempt_id, TestAttempt.user_id == learner.id)
    )
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise NotFoundError("Attempt not found")
    return {
        "attempt_id": str(attempt.id),
        "score": attempt.score,
        "max_score": attempt.max_score,
        "score_percent": attempt.score_percent,
        "passed": attempt.passed,
        "finished_at": attempt.finished_at,
    }


@router.get("/materials/{material_id}/download")
async def download_material(material_id: UUID, db: DB, learner: CurrentLearner):
    """Secure download — only for authenticated learners."""
    import os
    result = await db.execute(select(CourseMaterial).where(CourseMaterial.id == material_id))
    material = result.scalar_one_or_none()
    if not material or not material.file_path:
        raise NotFoundError("Material not found")
    if not os.path.exists(material.file_path):
        raise NotFoundError("File not found on disk")
    return FileResponse(
        material.file_path,
        filename=os.path.basename(material.file_path),
        content_disposition_type="attachment",
    )


@router.get("/materials/{material_id}/stream")
async def stream_material(material_id: UUID, token: str, db: DB):
    """Video streaming via X-Accel-Redirect — nginx serves the file directly, Python only checks auth."""
    import os, mimetypes
    from urllib.parse import quote
    from fastapi.responses import Response
    from app.core.security import decode_token
    from app.core.exceptions import UnauthorizedError
    from app.core.config import settings

    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or payload.get("role") != "learner":
        raise UnauthorizedError()

    result = await db.execute(select(CourseMaterial).where(CourseMaterial.id == material_id))
    material = result.scalar_one_or_none()
    if not material or not material.file_path:
        raise NotFoundError("Material not found")
    if not os.path.exists(material.file_path):
        raise NotFoundError("File not found on disk")

    filename = os.path.basename(material.file_path)
    media_type, _ = mimetypes.guess_type(filename)

    # Build X-Accel-Redirect path with URL-encoding for Cyrillic/special chars
    relative_path = material.file_path[len(settings.STORAGE_LOCAL_PATH):]
    # URL-encode each path segment to handle Cyrillic filenames
    encoded_path = "/".join(quote(seg, safe="") for seg in relative_path.replace("\\", "/").split("/"))
    x_accel_path = "/internal/storage" + encoded_path

    return Response(
        status_code=200,
        headers={
            "X-Accel-Redirect": x_accel_path,
            "Content-Type": media_type or "video/mp4",
            "Content-Disposition": f'inline; filename="{filename}"',
        },
    )
