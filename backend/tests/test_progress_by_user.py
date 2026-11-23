"""
Прогресс по сотрудникам: одна запись на человека со всеми его обучениями.
Раньше человек с тремя курсами занимал в списке три строки.
"""
from uuid import uuid4

from app.models.assignment import AssignmentStatus, UserCourseAssignment
from app.models.course import Course
from app.models.discipline import Discipline
from app.models.organization import Organization
from app.models.user import User
from tests.conftest import make_admin


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _setup(db):
    org_a = Organization(id=uuid4(), name="ТОО А", is_active=True)
    org_b = Organization(id=uuid4(), name="ТОО Б", is_active=True)
    db.add_all([org_a, org_b])
    discs = []
    for code, name in [("biot", "БиОТ"), ("ptm", "ПТМ"), ("pb", "ПромБез")]:
        d = Discipline(id=uuid4(), code=f"{code}_{uuid4().hex[:4]}", name=name)
        c = Course(id=uuid4(), discipline_id=d.id, name=f"Курс {name}")
        db.add_all([d, c])
        discs.append((d, c))
    await db.flush()

    def user(name, org):
        u = User(id=uuid4(), login=f"u_{uuid4().hex[:6]}", password_hash="x", full_name=name,
                 normalized_full_name=name.lower(), organization_id=org.id, is_active=True)
        db.add(u)
        return u

    ivanov = user("Иванов Иван", org_a)
    petrov = user("Петров Пётр", org_a)
    sidorov = user("Сидоров Сидор", org_b)
    await db.flush()
    statuses = [AssignmentStatus.passed, AssignmentStatus.failed, AssignmentStatus.assigned]
    for (d, c), st in zip(discs, statuses):
        db.add(UserCourseAssignment(user_id=ivanov.id, course_id=c.id, discipline_id=d.id, status=st))
    db.add(UserCourseAssignment(user_id=petrov.id, course_id=discs[0][1].id, discipline_id=discs[0][0].id,
                                status=AssignmentStatus.passed))
    db.add(UserCourseAssignment(user_id=sidorov.id, course_id=discs[0][1].id, discipline_id=discs[0][0].id,
                                status=AssignmentStatus.in_progress))
    await db.flush()
    return org_a, org_b


async def test_one_row_per_person_with_all_trainings(http, db):
    await _setup(db)
    _, token = await make_admin(db)
    await db.commit()

    resp = await http.get("/api/v1/admin/progress/by-user", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.headers["x-total-count"] == "3"
    rows = resp.json()
    assert [r["user"]["full_name"] for r in rows] == ["Иванов Иван", "Петров Пётр", "Сидоров Сидор"]
    ivanov = rows[0]
    assert len(ivanov["assignments"]) == 3
    assert ivanov["summary"] == {"total": 3, "passed": 1, "failed": 1, "assigned": 1, "in_progress": 0}
    assert {a["discipline"]["name"] for a in ivanov["assignments"]} == {"БиОТ", "ПТМ", "ПромБез"}


async def test_status_filter_keeps_person_once_and_shows_matching_trainings(http, db):
    await _setup(db)
    _, token = await make_admin(db)
    await db.commit()

    resp = await http.get("/api/v1/admin/progress/by-user", headers=auth(token), params={"status": "passed"})
    rows = resp.json()
    assert [r["user"]["full_name"] for r in rows] == ["Иванов Иван", "Петров Пётр"]
    assert all(a["status"] == "passed" for r in rows for a in r["assignments"])


async def test_paging_is_by_person(http, db):
    await _setup(db)
    _, token = await make_admin(db)
    await db.commit()

    page = await http.get("/api/v1/admin/progress/by-user", headers=auth(token), params={"limit": 1})
    assert page.headers["x-total-count"] == "3"
    rows = page.json()
    assert len(rows) == 1 and len(rows[0]["assignments"]) == 3  # обучения человека не разрезаны


async def test_org_viewer_sees_only_own_organization(http, db):
    org_a, _ = await _setup(db)
    _, token = await make_admin(db, organization_id=org_a.id, is_org_viewer=True)
    await db.commit()

    rows = (await http.get("/api/v1/admin/progress/by-user", headers=auth(token))).json()
    assert {r["user"]["full_name"] for r in rows} == {"Иванов Иван", "Петров Пётр"}


async def test_search(http, db):
    await _setup(db)
    _, token = await make_admin(db)
    await db.commit()
    rows = (await http.get("/api/v1/admin/progress/by-user", headers=auth(token), params={"search": "петр"})).json()
    assert [r["user"]["full_name"] for r in rows] == ["Петров Пётр"]
