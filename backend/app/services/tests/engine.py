"""
Test engine service.
Calculates test result from submitted answers.
"""
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.test import TestQuestionOption


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

        # Build correct answer map
        correct_map: dict[str, str] = {}
        for q in test.questions:
            for opt in q.options:
                if opt.is_correct:
                    correct_map[str(q.id)] = str(opt.id)

        correct_count = 0
        total = len(test.questions)

        for ans in answers:
            q_id_raw = ans.get("question_id")
            opt_id_raw = ans.get("option_id")

            # Convert to UUID objects (model columns are Mapped[uuid.UUID])
            try:
                q_uuid = UUID(str(q_id_raw)) if q_id_raw else None
            except (ValueError, AttributeError):
                q_uuid = None

            try:
                opt_uuid = UUID(str(opt_id_raw)) if opt_id_raw else None
            except (ValueError, AttributeError):
                opt_uuid = None

            if q_uuid is None:
                continue  # skip malformed answers

            q_id_str = str(q_uuid)
            opt_id_str = str(opt_uuid) if opt_uuid else None
            is_correct = opt_id_str is not None and correct_map.get(q_id_str) == opt_id_str

            answer_record = TestAttemptAnswer(
                attempt_id=attempt.id,
                question_id=q_uuid,
                selected_option_id=opt_uuid,
                is_correct=is_correct,
            )
            self.db.add(answer_record)

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
            "finished_at": attempt.finished_at.isoformat(),
        }
