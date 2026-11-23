"""
Прохождение теста обучающимся: подсчёт баллов и защита от обхода.

Раньше сервер считал каждый присланный ответ: отправив на каждый вопрос все
варианты сразу (или правильный ответ N раз), можно было получить 100% без
знаний. Время теста на сервере не проверялось вовсе.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.models.assignment import AssignmentStatus, UserCourseAssignment
from app.models.attempt import TestAttempt
from app.models.course import Course
from app.models.discipline import Discipline
from app.models.test import Test, TestQuestion, TestQuestionOption
from app.models.user import User


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _setup(db, n_questions=3, pass_score=60, max_attempts=0, time_limit=0):
    """Обучающийся + курс с тестом: в каждом вопросе варианты «Верно» (правильный) и «Неверно»."""
    disc = Discipline(id=uuid4(), code=f"D{uuid4().hex[:5]}", name="Дисциплина")
    course = Course(id=uuid4(), discipline_id=disc.id, name="Курс")
    user = User(id=uuid4(), login=f"l_{uuid4().hex[:6]}", password_hash=hash_password("x"),
                full_name="Обучающийся", normalized_full_name="обучающийся", is_active=True)
    db.add_all([disc, course, user])
    await db.flush()
    test = Test(id=uuid4(), course_id=course.id, pass_score=pass_score,
                max_attempts=max_attempts, time_limit_minutes=time_limit)
    db.add(test)
    await db.flush()
    questions = []
    for i in range(n_questions):
        q = TestQuestion(id=uuid4(), test_id=test.id, text=f"Вопрос {i}", sort_order=i)
        db.add(q)
        await db.flush()
        right = TestQuestionOption(id=uuid4(), question_id=q.id, text="Верно", is_correct=True, sort_order=0)
        wrong = TestQuestionOption(id=uuid4(), question_id=q.id, text="Неверно", is_correct=False, sort_order=1)
        db.add_all([right, wrong])
        questions.append((q, right, wrong))
    assignment = UserCourseAssignment(id=uuid4(), user_id=user.id, course_id=course.id,
                                      discipline_id=disc.id, status=AssignmentStatus.assigned)
    db.add(assignment)
    await db.commit()
    token = create_access_token(str(user.id), {"role": "learner"})
    return token, assignment, questions


async def _start(http, token, assignment):
    resp = await http.post(f"/api/v1/learner/me/courses/{assignment.id}/start-test", headers=auth(token))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # Правильные ответы при старте наружу не уходят.
    assert "is_correct" not in resp.text
    return data["attempt_id"]


async def _submit(http, token, attempt_id, answers):
    return await http.post(f"/api/v1/learner/me/tests/{attempt_id}/submit",
                           headers=auth(token), json={"answers": answers})


def _ans(q, opt):
    return {"question_id": str(q.id), "option_id": str(opt.id)}


async def test_honest_all_correct_passes(http, db):
    token, assignment, qs = await _setup(db)
    attempt_id = await _start(http, token, assignment)
    resp = await _submit(http, token, attempt_id, [_ans(q, r) for q, r, _ in qs])
    assert resp.status_code == 200, resp.text
    assert resp.json()["score_percent"] == 100 and resp.json()["passed"] is True


async def test_honest_all_wrong_fails(http, db):
    token, assignment, qs = await _setup(db)
    attempt_id = await _start(http, token, assignment)
    resp = await _submit(http, token, attempt_id, [_ans(q, w) for q, _, w in qs])
    assert resp.json()["score_percent"] == 0 and resp.json()["passed"] is False


async def test_sending_every_option_does_not_pass(http, db):
    """Обход: на каждый вопрос все варианты — засчитывается только первый ответ."""
    token, assignment, qs = await _setup(db)
    attempt_id = await _start(http, token, assignment)
    answers = []
    for q, right, wrong in qs:
        answers += [_ans(q, wrong), _ans(q, right)]
    resp = await _submit(http, token, attempt_id, answers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["score"] == 0
    assert resp.json()["passed"] is False


async def test_repeating_one_correct_answer_counts_once(http, db):
    """Обход: один известный правильный ответ, повторённый N раз."""
    token, assignment, qs = await _setup(db, n_questions=3)
    attempt_id = await _start(http, token, assignment)
    q0, right0, _ = qs[0]
    resp = await _submit(http, token, attempt_id, [_ans(q0, right0)] * 3)
    assert resp.json()["score"] == 1
    assert resp.json()["score_percent"] == 33
    assert resp.json()["passed"] is False


async def test_option_from_another_question_is_not_correct(http, db):
    token, assignment, qs = await _setup(db, n_questions=2)
    attempt_id = await _start(http, token, assignment)
    (q0, _, _), (q1, right1, _) = qs
    resp = await _submit(http, token, attempt_id, [_ans(q0, right1), _ans(q1, right1)])
    assert resp.json()["score"] == 1


async def test_foreign_question_ids_ignored(http, db):
    token, assignment, qs = await _setup(db, n_questions=2)
    attempt_id = await _start(http, token, assignment)
    fake = {"question_id": str(uuid4()), "option_id": str(uuid4())}
    resp = await _submit(http, token, attempt_id, [fake] * 10 + [_ans(qs[0][0], qs[0][1])])
    assert resp.json()["score"] == 1 and resp.json()["max_score"] == 2


async def test_submit_after_time_limit_fails(http, db):
    """Сдача сильно позже лимита времени (с запасом на сеть) — не засчитывается."""
    token, assignment, qs = await _setup(db, time_limit=10)
    attempt_id = await _start(http, token, assignment)
    attempt = (await db.execute(select(TestAttempt).where(TestAttempt.id == attempt_id))).scalar_one()
    attempt.started_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    await db.commit()
    resp = await _submit(http, token, attempt_id, [_ans(q, r) for q, r, _ in qs])
    assert resp.status_code == 200, resp.text
    assert resp.json()["passed"] is False
    assert resp.json()["score"] == 0


async def test_submit_slightly_late_still_counts(http, db):
    """Автосдача по таймеру приходит на секунды позже — это нормально."""
    token, assignment, qs = await _setup(db, time_limit=10)
    attempt_id = await _start(http, token, assignment)
    attempt = (await db.execute(select(TestAttempt).where(TestAttempt.id == attempt_id))).scalar_one()
    attempt.started_at = datetime.now(timezone.utc) - timedelta(minutes=10, seconds=30)
    await db.commit()
    resp = await _submit(http, token, attempt_id, [_ans(q, r) for q, r, _ in qs])
    assert resp.json()["passed"] is True


async def test_cannot_submit_twice(http, db):
    token, assignment, qs = await _setup(db)
    attempt_id = await _start(http, token, assignment)
    await _submit(http, token, attempt_id, [_ans(q, w) for q, _, w in qs])
    resp = await _submit(http, token, attempt_id, [_ans(q, r) for q, r, _ in qs])
    assert resp.status_code == 403


async def test_max_attempts_marks_failed_and_blocks_new_attempt(http, db):
    token, assignment, qs = await _setup(db, max_attempts=1)
    attempt_id = await _start(http, token, assignment)
    await _submit(http, token, attempt_id, [_ans(q, w) for q, _, w in qs])
    await db.refresh(assignment)
    assert assignment.status == AssignmentStatus.failed
    resp = await http.post(f"/api/v1/learner/me/courses/{assignment.id}/start-test", headers=auth(token))
    assert resp.status_code == 403


async def test_other_learner_cannot_submit_my_attempt(http, db):
    token, assignment, qs = await _setup(db)
    attempt_id = await _start(http, token, assignment)
    other_token, _, _ = await _setup(db)
    resp = await _submit(http, other_token, attempt_id, [_ans(q, r) for q, r, _ in qs])
    assert resp.status_code == 404
