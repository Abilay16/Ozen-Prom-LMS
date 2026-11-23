"""
Данные для e2e-тестов (Playwright). Только для dev/CI — НЕ запускать на проде.

Создаёт (идемпотентно) и сбрасывает состояние обучающегося перед прогоном:
  e2e_admin   / E2e-Admin-123   — суперадмин
  e2e_chair   / E2e-Chair-123   — член комиссии (председатель)
  e2e_viewer  / E2e-View-123    — просмотр по организации «ТОО E2E Тест»
  e2e_learner / E2e-Learn-123   — обучающийся, назначен курс с тестом
                                  (3 вопроса, правильный ответ — «Верно»)
  e2e_other   — сотрудник другой организации (не должен быть виден viewer'у)
  Удостоверение БиОТ E2E-BIOT-0001 (id 00000000-0000-4000-8000-00000000e2e1)

Usage:
  docker compose exec backend python -m scripts.seed_e2e
"""
import asyncio
import os
import sys
import uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import AsyncSessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.assignment import AssignmentStatus, UserCourseAssignment  # noqa: E402
from app.models.attempt import TestAttempt, TestAttemptAnswer  # noqa: E402
from app.models.certificate import Certificate  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.discipline import Discipline  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.test import Test, TestQuestion, TestQuestionOption  # noqa: E402
from app.models.training_type import TrainingType  # noqa: E402
from app.models.user import AdminUser, User  # noqa: E402

CERT_ID = uuid.UUID("00000000-0000-4000-8000-00000000e2e1")


async def one(db, stmt):
    return (await db.execute(stmt)).scalar_one_or_none()


async def org(db, name):
    row = await one(db, select(Organization).where(Organization.name == name))
    if not row:
        row = Organization(name=name, short_name=name[:20], bin="000000000000")
        db.add(row)
        await db.flush()
    return row


async def admin(db, login, password, full_name, **kw):
    row = await one(db, select(AdminUser).where(AdminUser.login == login))
    if not row:
        row = AdminUser(login=login, full_name=full_name, password_hash=hash_password(password), **kw)
        db.add(row)
        await db.flush()
    return row


async def learner(db, login, password, full_name, org_id):
    row = await one(db, select(User).where(User.login == login))
    if not row:
        row = User(
            login=login,
            password_hash=hash_password(password),
            plain_password=password,
            full_name=full_name,
            normalized_full_name=full_name.lower(),
            organization_id=org_id,
            position_raw="Инженер",
            is_active=True,
            verify_token=uuid.uuid4(),
        )
        db.add(row)
        await db.flush()
    return row


async def main():
    if settings.ENVIRONMENT == "production":
        sys.exit("seed_e2e: отказ — ENVIRONMENT=production")

    async with AsyncSessionLocal() as db:
        org_main = await org(db, "ТОО E2E Тест")
        org_other = await org(db, "ТОО E2E Чужая")

        await admin(db, "e2e_admin", "E2e-Admin-123", "E2E Суперадмин", is_superadmin=True)
        await admin(db, "e2e_chair", "E2e-Chair-123", "E2E Председатель",
                    is_commission_eligible=True, position_title="Председатель комиссии")
        await admin(db, "e2e_viewer", "E2e-View-123", "E2E Наблюдатель",
                    is_org_viewer=True, organization_id=org_main.id)

        user = await learner(db, "e2e_learner", "E2e-Learn-123", "Тестов Тест Тестович", org_main.id)
        await learner(db, "e2e_other", "E2e-Other-123", "Чужой Сотрудник Иванович", org_other.id)

        disc = await one(db, select(Discipline).where(Discipline.code == "e2e"))
        if not disc:
            disc = Discipline(code="e2e", name="E2E дисциплина", description="Для автотестов", is_active=True)
            db.add(disc)
            await db.flush()

        course = await one(db, select(Course).where(Course.discipline_id == disc.id))
        if not course:
            course = Course(discipline_id=disc.id, name="E2E курс", description="Для автотестов",
                            duration_hours=1, is_active=True)
            db.add(course)
            await db.flush()

        test = await one(db, select(Test).where(Test.course_id == course.id))
        if not test:
            test = Test(course_id=course.id, pass_score=60, max_attempts=0,
                        time_limit_minutes=0, show_correct_answers=True)
            db.add(test)
            await db.flush()
            for i in range(3):
                q = TestQuestion(test_id=test.id, text=f"Вопрос {i + 1}: выберите «Верно»", sort_order=i)
                db.add(q)
                await db.flush()
                for j, text in enumerate(["Верно", "Неверно"]):
                    db.add(TestQuestionOption(question_id=q.id, text=text, is_correct=(j == 0), sort_order=j))

        # Сброс прогресса обучающегося — тест можно проходить заново при каждом прогоне.
        attempt_ids = select(TestAttempt.id).where(TestAttempt.user_id == user.id)
        await db.execute(delete(TestAttemptAnswer).where(TestAttemptAnswer.attempt_id.in_(attempt_ids)))
        await db.execute(delete(TestAttempt).where(TestAttempt.user_id == user.id))
        assignment = await one(db, select(UserCourseAssignment).where(
            UserCourseAssignment.user_id == user.id, UserCourseAssignment.course_id == course.id))
        if not assignment:
            assignment = UserCourseAssignment(user_id=user.id, course_id=course.id, discipline_id=disc.id)
            db.add(assignment)
        assignment.status = AssignmentStatus.assigned
        assignment.completed_at = None

        biot = await one(db, select(TrainingType).where(TrainingType.code == "biot"))
        if not await one(db, select(Certificate).where(Certificate.id == CERT_ID)):
            today = date.today()
            db.add(Certificate(
                id=CERT_ID,
                certificate_number="E2E-BIOT-0001",
                user_id=user.id,
                training_type_id=biot.id if biot else None,
                full_name=user.full_name,
                organization_name=org_main.name,
                position=user.position_raw,
                issued_date=today,
                valid_until=today + timedelta(days=365),
                is_renewal=False,
            ))

        await db.commit()
    print("seed_e2e: ok")


if __name__ == "__main__":
    asyncio.run(main())
