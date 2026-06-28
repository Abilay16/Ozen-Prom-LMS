"""
Demo seed script — создаёт тестового пользователя для записи экрана.

Создаёт (идемпотентно):
  Организация: ТОО «Озен-Пром Демо»

  Дисциплины (если нет): БиОТ, ПТМ, ПромБез

  Курсы с лёгкими тестами (5 вопросов, правильный ответ — первый):
    - Безопасность и охрана труда (БиОТ)
    - Пожарно-техническая минимум (ПТМ)
    - Промышленная безопасность (ПромБез)

  Пользователь:
    demo.user / Demo1234 — Алибеков Данияр Маратович

  Назначения + завершённые тесты (100% — сдал все три)

  Удостоверения: БиОТ, ПТМ, ПромБез

  Медосмотр: годен, 2026-03-10

Usage:
  docker compose exec backend python -m scripts.seed_demo_user
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.organization import Organization
from app.models.discipline import Discipline
from app.models.course import Course
from app.models.test import Test, TestQuestion, TestQuestionOption
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.certificate import Certificate
from app.models.training_type import TrainingType
from app.models.medical_exam import MedicalExam


# ── helpers ───────────────────────────────────────────────────────────────────

async def get_or_create_org(db, name):
    row = (await db.execute(select(Organization).where(Organization.name == name))).scalar_one_or_none()
    if row:
        print(f"  [skip] org '{name}' already exists")
        return row
    row = Organization(name=name, short_name="ОПД", bin="999999999999")
    db.add(row)
    await db.flush()
    print(f"  [+] org '{name}'")
    return row


async def get_or_create_discipline(db, code, name, description):
    row = (await db.execute(select(Discipline).where(Discipline.code == code))).scalar_one_or_none()
    if row:
        print(f"  [skip] discipline '{code}' already exists")
        return row
    row = Discipline(code=code, name=name, description=description, is_active=True)
    db.add(row)
    await db.flush()
    print(f"  [+] discipline '{code}' — {name}")
    return row


async def get_or_create_course(db, discipline_id, name):
    row = (await db.execute(
        select(Course).where(Course.discipline_id == discipline_id, Course.name == name)
    )).scalar_one_or_none()
    if row:
        print(f"  [skip] course '{name}' already exists")
        return row
    row = Course(
        discipline_id=discipline_id,
        name=name,
        description=f"Демонстрационный курс: {name}",
        duration_hours=8,
        is_active=True,
    )
    db.add(row)
    await db.flush()
    print(f"  [+] course '{name}'")
    return row


async def get_or_create_test(db, course_id, questions_data):
    """Create test with easy questions. questions_data: list of (question_text, [options], correct_index)"""
    existing = (await db.execute(select(Test).where(Test.course_id == course_id))).scalar_one_or_none()
    if existing:
        print(f"  [skip] test for course already exists")
        return existing

    test = Test(
        course_id=course_id,
        pass_score=60,
        max_attempts=0,
        time_limit_minutes=0,
        show_correct_answers=True,
    )
    db.add(test)
    await db.flush()

    for i, (qtext, options, correct_idx) in enumerate(questions_data):
        q = TestQuestion(test_id=test.id, text=qtext, sort_order=i)
        db.add(q)
        await db.flush()
        for j, opt_text in enumerate(options):
            db.add(TestQuestionOption(
                question_id=q.id,
                text=opt_text,
                is_correct=(j == correct_idx),
                sort_order=j,
            ))

    await db.flush()
    print(f"  [+] test with {len(questions_data)} questions")
    return test


async def get_or_create_user(db, login, password, full_name, org_id):
    row = (await db.execute(select(User).where(User.login == login))).scalar_one_or_none()
    if row:
        print(f"  [skip] user '{login}' already exists")
        return row
    import uuid
    row = User(
        login=login,
        password_hash=hash_password(password),
        plain_password=password,
        full_name=full_name,
        normalized_full_name=full_name.lower(),
        organization_id=org_id,
        position_raw="Инженер по охране труда",
        is_active=True,
        verify_token=uuid.uuid4(),
    )
    db.add(row)
    await db.flush()
    print(f"  [+] user '{login}'  pw='{password}'")
    return row


async def get_or_create_assignment(db, user_id, course_id, discipline_id):
    row = (await db.execute(
        select(UserCourseAssignment).where(
            UserCourseAssignment.user_id == user_id,
            UserCourseAssignment.course_id == course_id,
        )
    )).scalar_one_or_none()
    if row:
        print(f"  [skip] assignment already exists (status={row.status})")
        return row
    row = UserCourseAssignment(
        user_id=user_id,
        course_id=course_id,
        discipline_id=discipline_id,
        status=AssignmentStatus.assigned,
    )
    db.add(row)
    await db.flush()
    print(f"  [+] assignment created")
    return row


async def complete_assignment(db, user_id, assignment, test):
    """Mark assignment as passed and create a completed test attempt."""
    existing = (await db.execute(
        select(TestAttempt).where(
            TestAttempt.assignment_id == assignment.id,
            TestAttempt.passed == True,
        )
    )).scalar_one_or_none()
    if existing:
        print(f"  [skip] passed attempt already exists")
        return existing

    now = datetime.now(timezone.utc)
    attempt = TestAttempt(
        user_id=user_id,
        assignment_id=assignment.id,
        test_id=test.id,
        attempt_number=1,
        status=AttemptStatus.completed,
        score=5,
        max_score=5,
        score_percent=100,
        passed=True,
        started_at=now - timedelta(minutes=10),
        finished_at=now,
    )
    db.add(attempt)
    await db.flush()

    # Load questions with options and create correct answers
    from sqlalchemy.orm import selectinload
    test_loaded = (await db.execute(
        select(Test)
        .options(
            selectinload(Test.questions).selectinload(TestQuestion.options)
        )
        .where(Test.id == test.id)
    )).scalar_one()

    for q in test_loaded.questions:
        correct_opt = next((o for o in q.options if o.is_correct), q.options[0] if q.options else None)
        if correct_opt:
            db.add(TestAttemptAnswer(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option_id=correct_opt.id,
                is_correct=True,
            ))

    # Update assignment status
    assignment.status = AssignmentStatus.passed
    assignment.completed_at = now
    await db.flush()
    print(f"  [+] attempt completed (100%, passed)")
    return attempt


async def get_training_type(db, code):
    row = (await db.execute(select(TrainingType).where(TrainingType.code == code))).scalar_one_or_none()
    return row


async def create_certificate(db, user, org_name, training_type, cert_number):
    existing = (await db.execute(
        select(Certificate).where(Certificate.certificate_number == cert_number)
    )).scalar_one_or_none()
    if existing:
        print(f"  [skip] certificate '{cert_number}' already exists")
        return existing

    issued = date(2026, 6, 1)
    validity = training_type.validity_years if training_type else 1
    valid_until = date(issued.year + validity, issued.month, issued.day)

    cert = Certificate(
        certificate_number=cert_number,
        user_id=user.id,
        training_type_id=training_type.id if training_type else None,
        full_name=user.full_name,
        organization_name=org_name,
        position=user.position_raw,
        issued_date=issued,
        valid_until=valid_until,
        is_renewal=False,
    )
    db.add(cert)
    await db.flush()
    print(f"  [+] certificate '{cert_number}'  valid until {valid_until}")
    return cert


async def create_medical_exam(db, user, org_id):
    existing = (await db.execute(
        select(MedicalExam).where(MedicalExam.user_id == user.id)
    )).scalar_one_or_none()
    if existing:
        print(f"  [skip] medical exam already exists")
        return existing

    med = MedicalExam(
        user_id=user.id,
        organization_id=org_id,
        full_name=user.full_name,
        birth_date=date(1990, 5, 15),
        gender="муж",
        workplace="Производственный участок №3",
        position=user.position_raw,
        icd10_group="Группа I — здоров",
        fit_for_work=True,
        exam_date=date(2026, 3, 10),
        source_file="medspr_2026_03.xlsx",
    )
    db.add(med)
    await db.flush()
    print(f"  [+] medical exam (godeen, 2026-03-10)")
    return med


# ── test data ─────────────────────────────────────────────────────────────────

BIOT_QUESTIONS = [
    (
        "Что является основной целью инструктажа по безопасности труда?",
        ["Ознакомление работника с безопасными методами работы", "Выдача спецодежды", "Заполнение журнала", "Подготовка отчёта"],
        0,
    ),
    (
        "Какой документ подтверждает прохождение вводного инструктажа?",
        ["Подпись в журнале инструктажей", "Трудовой договор", "Медицинская справка", "Паспорт"],
        0,
    ),
    (
        "Кто несёт ответственность за состояние охраны труда на предприятии?",
        ["Работодатель", "Только работник", "Профсоюз", "Страховая компания"],
        0,
    ),
    (
        "При несчастном случае на производстве первым делом необходимо:",
        ["Оказать первую помощь пострадавшему и вызвать скорую", "Продолжить работу", "Составить акт", "Позвонить родственникам"],
        0,
    ),
    (
        "Как часто проводится повторный инструктаж по охране труда?",
        ["Не реже одного раза в 6 месяцев", "Один раз в 5 лет", "Ежедневно", "По требованию работника"],
        0,
    ),
]

PTM_QUESTIONS = [
    (
        "Что нужно сделать при обнаружении пожара в первую очередь?",
        ["Сообщить о пожаре и начать эвакуацию", "Продолжать работу", "Искать огнетушитель", "Открыть окна"],
        0,
    ),
    (
        "Какой класс пожара соответствует горению твёрдых веществ?",
        ["Класс A", "Класс B", "Класс C", "Класс D"],
        0,
    ),
    (
        "Где должны располагаться огнетушители?",
        ["В доступных и видимых местах", "В шкафу под замком", "На складе", "На улице"],
        0,
    ),
    (
        "Что такое эвакуационный выход?",
        ["Выход, ведущий к безопасной зоне при пожаре", "Служебный вход", "Аварийный люк на крыше", "Запасной склад"],
        0,
    ),
    (
        "Как часто проводится противопожарный инструктаж?",
        ["Не реже одного раза в год", "Раз в 5 лет", "Ежедневно", "Только при приёме на работу"],
        0,
    ),
]

PROMBEZ_QUESTIONS = [
    (
        "Что такое опасный производственный объект (ОПО)?",
        ["Объект, на котором ведутся работы с опасными веществами или оборудованием", "Любое предприятие", "Строительный объект", "Офисное здание"],
        0,
    ),
    (
        "Кто имеет право работать на ОПО?",
        ["Лица, прошедшие аттестацию по промышленной безопасности", "Любые работники", "Только молодые специалисты", "Только руководители"],
        0,
    ),
    (
        "Как часто проводится аттестация по промышленной безопасности?",
        ["Не реже одного раза в 5 лет", "Ежегодно", "Один раз при приёме", "Раз в 10 лет"],
        0,
    ),
    (
        "Что обозначает знак «Опасность взрыва»?",
        ["Зону с риском взрыва, требующую особых мер безопасности", "Запрет на вход", "Место хранения инструментов", "Точку заземления"],
        0,
    ),
    (
        "При аварии на ОПО работник обязан:",
        ["Немедленно сообщить руководителю и покинуть опасную зону", "Устранить аварию самостоятельно", "Продолжать работу", "Дождаться конца смены"],
        0,
    ),
]


# ── main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n═══════════════════════════════════════════════")
    print("  Ozen-Prom LMS  — Demo User seed")
    print("═══════════════════════════════════════════════\n")

    async with AsyncSessionLocal() as db:

        # ── Organization ──────────────────────────────────────────────────────
        print("▶ Organization:")
        org = await get_or_create_org(db, "ТОО «Озен-Пром Демо»")

        # ── Disciplines ───────────────────────────────────────────────────────
        print("\n▶ Disciplines:")
        disc_biot   = await get_or_create_discipline(db, "biot",    "БиОТ",    "Безопасность и охрана труда")
        disc_ptm    = await get_or_create_discipline(db, "ptm",     "ПТМ",     "Пожарно-техническая минимум")
        disc_prombez = await get_or_create_discipline(db, "prombez", "ПромБез", "Промышленная безопасность")

        # ── Courses ───────────────────────────────────────────────────────────
        print("\n▶ Courses:")
        course_biot   = await get_or_create_course(db, disc_biot.id,    "Безопасность и охрана труда (базовый)")
        course_ptm    = await get_or_create_course(db, disc_ptm.id,     "Пожарно-технический минимум (базовый)")
        course_prombez = await get_or_create_course(db, disc_prombez.id, "Промышленная безопасность (базовый)")

        # ── Tests ─────────────────────────────────────────────────────────────
        print("\n▶ Tests:")
        test_biot   = await get_or_create_test(db, course_biot.id,    BIOT_QUESTIONS)
        test_ptm    = await get_or_create_test(db, course_ptm.id,     PTM_QUESTIONS)
        test_prombez = await get_or_create_test(db, course_prombez.id, PROMBEZ_QUESTIONS)

        # ── User ──────────────────────────────────────────────────────────────
        print("\n▶ Demo user:")
        user = await get_or_create_user(db, "demo.user", "Demo1234",
                                         "Алибеков Данияр Маратович", org.id)

        # ── Assignments ───────────────────────────────────────────────────────
        print("\n▶ Assignments:")
        asgn_biot   = await get_or_create_assignment(db, user.id, course_biot.id,   disc_biot.id)
        asgn_ptm    = await get_or_create_assignment(db, user.id, course_ptm.id,    disc_ptm.id)
        asgn_prombez = await get_or_create_assignment(db, user.id, course_prombez.id, disc_prombez.id)

        # ── Complete tests ────────────────────────────────────────────────────
        print("\n▶ Completing tests (100%):")
        await complete_assignment(db, user.id, asgn_biot,    test_biot)
        await complete_assignment(db, user.id, asgn_ptm,     test_ptm)
        await complete_assignment(db, user.id, asgn_prombez, test_prombez)

        # ── Training types ────────────────────────────────────────────────────
        print("\n▶ Training types:")
        tt_biot    = await get_training_type(db, "biot")
        tt_ptm     = await get_training_type(db, "ptm")
        tt_prombez = await get_training_type(db, "prombez")
        for code, tt in [("biot", tt_biot), ("ptm", tt_ptm), ("prombez", tt_prombez)]:
            if tt:
                print(f"  ok: {code} — {tt.name_ru}")
            else:
                print(f"  WARN: training_type '{code}' not found — run migrations first")

        # ── Certificates ──────────────────────────────────────────────────────
        print("\n▶ Certificates:")
        if tt_biot:
            await create_certificate(db, user, org.name, tt_biot,    "DEMO-BIOT-2026-001")
        if tt_ptm:
            await create_certificate(db, user, org.name, tt_ptm,     "DEMO-PTM-2026-001")
        if tt_prombez:
            await create_certificate(db, user, org.name, tt_prombez, "DEMO-PROMBEZ-2026-001")

        # ── Medical exam ──────────────────────────────────────────────────────
        print("\n▶ Medical exam:")
        await create_medical_exam(db, user, org.id)

        await db.commit()

    print("""
═══════════════════════════════════════════════
  ГОТОВО! Демо-пользователь создан.
═══════════════════════════════════════════════

  ТЕСТОВЫЙ ПОЛЬЗОВАТЕЛЬ:
  ┌─────────────────────────────────────────────────────────────────┐
  │  login     │  demo.user                                         │
  │  пароль    │  Demo1234                                          │
  │  ФИО       │  Алибеков Данияр Маратович                         │
  │  организ.  │  ТОО «Озен-Пром Демо»                              │
  │  должность │  Инженер по охране труда                           │
  └─────────────────────────────────────────────────────────────────┘

  В КАБИНЕТЕ ПОЛЬЗОВАТЕЛЯ:
    📚 Мои курсы:
       • Безопасность и охрана труда (базовый)  — СДАН (100%)
       • Пожарно-технический минимум (базовый)   — СДАН (100%)
       • Промышленная безопасность (базовый)     — СДАН (100%)

    📜 Удостоверения:
       • DEMO-BIOT-2026-001    — БиОТ    (действ. 1 год)
       • DEMO-PTM-2026-001     — ПТМ     (действ. 3 года)
       • DEMO-PROMBEZ-2026-001 — ПромБез (действ. 1 год)

    🏥 Медосмотр:
       • 10.03.2026 — Годен, группа I — здоров

  СЦЕНАРИЙ ЗАПИСИ ЭКРАНА:
    1. Открыть http://localhost:5173/login
    2. Войти как demo.user / Demo1234
    3. Показать страницу «Мои курсы» — три курса со статусом «Сдан»
    4. Зайти в курс БиОТ — показать тест и результат
    5. Перейти на страницу «Удостоверения»
       → три удостоверения (БиОТ, ПТМ, ПромБез) + QR-карточка
       → блок «Медицинский осмотр» — годен
""")


if __name__ == "__main__":
    asyncio.run(main())
