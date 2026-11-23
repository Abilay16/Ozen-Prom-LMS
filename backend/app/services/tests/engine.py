"""
Test engine service.
Calculates test result from submitted answers.
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.assignment import UserCourseAssignment, AssignmentStatus


LATE_SUBMIT_GRACE = timedelta(minutes=2)


def _as_uuid(raw) -> UUID | None:
    try:
        return UUID(str(raw)) if raw else None
    except (ValueError, AttributeError):
        return None


class TestEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_result(self, attempt: TestAttempt, answers: list[dict]) -> dict:
        """
        answers = [{"question_id": "...", "option_id": "..."}]
        """
        # Load test with questions
        from app.models.test import Test, TestQuestion
        test_result = await self.db.execute(
            select(Test)
            .options(selectinload(Test.questions).selectinload(TestQuestion.options))
            .where(Test.id == attempt.test_id)
        )
        test = test_result.scalar_one()

        # Вопросы этого теста и их варианты: {question_id: {option_id: is_correct}}
        options_by_question: dict[UUID, dict[UUID, bool]] = {
            q.id: {o.id: bool(o.is_correct) for o in q.options} for q in test.questions
        }

        correct_count = 0
        total = len(test.questions)

        # Просрочка: таймер на клиенте автосдаёт тест, поэтому даём запас на
        # сеть и медленный телефон; всё, что сильно позже лимита, — подмена.
        overdue = False
        if test.time_limit_minutes and attempt.started_at:
            deadline = attempt.started_at + timedelta(minutes=test.time_limit_minutes) + LATE_SUBMIT_GRACE
            overdue = datetime.now(timezone.utc) > deadline

        # Один ответ на вопрос: учитываем только первый ответ на каждый вопрос
        # этого теста, вариант должен принадлежать именно этому вопросу.
        # Раньше можно было прислать все варианты сразу и получить 100%.
        seen: set[UUID] = set()
        for ans in answers if not overdue else []:
            q_uuid = _as_uuid(ans.get("question_id"))
            opt_uuid = _as_uuid(ans.get("option_id"))
            if q_uuid is None or q_uuid not in options_by_question or q_uuid in seen:
                continue
            seen.add(q_uuid)

            q_options = options_by_question[q_uuid]
            if opt_uuid not in q_options:
                opt_uuid = None  # чужой/выдуманный вариант = нет ответа
            is_correct = opt_uuid is not None and q_options[opt_uuid]

            self.db.add(TestAttemptAnswer(
                attempt_id=attempt.id,
                question_id=q_uuid,
                selected_option_id=opt_uuid,
                is_correct=is_correct,
            ))
            if is_correct:
                correct_count += 1

        score_percent = round((correct_count / total) * 100) if total > 0 else 0
        passed = score_percent >= test.pass_score

        attempt.score = correct_count
        attempt.max_score = total
        attempt.score_percent = score_percent
        attempt.passed = passed
        attempt.status = AttemptStatus.completed
        attempt.finished_at = datetime.now(timezone.utc)

        # Update assignment status
        assignment_result = await self.db.execute(
            select(UserCourseAssignment).where(UserCourseAssignment.id == attempt.assignment_id)
        )
        assignment = assignment_result.scalar_one()
        if passed:
            assignment.status = AssignmentStatus.passed
            assignment.completed_at = datetime.now(timezone.utc)
        else:
            # Check if max attempts reached
            from app.models.attempt import TestAttempt as TA
            from sqlalchemy import func
            count_result = await self.db.execute(
                select(func.count()).where(
                    TA.assignment_id == attempt.assignment_id,
                    TA.status == AttemptStatus.completed,
                )
            )
            completed_count = count_result.scalar()
            if test.max_attempts > 0 and completed_count >= test.max_attempts:
                assignment.status = AssignmentStatus.failed

        await self.db.flush()

        return {
            "attempt_id": str(attempt.id),
            "score": correct_count,
            "max_score": total,
            "score_percent": score_percent,
            "passed": passed,
            "pass_score": test.pass_score,
            "assignment_id": str(attempt.assignment_id),
            "finished_at": attempt.finished_at.isoformat(),
        }
