"""
Импорт медосмотров: запись о годности не должна уйти однофамильцу,
повторная загрузка файла не дублирует записи.
"""
import io
from datetime import date
from uuid import uuid4

import openpyxl
from sqlalchemy import func, select

from app.models.medical_exam import MedicalExam
from app.models.organization import Organization
from app.models.user import User
from tests.conftest import make_admin


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _file(rows) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Список работников, прошедших медосмотр"])
    ws.append(["№", "ФИО", "Дата рождения", "Занимаемая должность", "Профпри (годен)", "Дата прохождения"])
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


async def _user(db, name, org_id=None):
    u = User(id=uuid4(), login=f"u_{uuid4().hex[:6]}", password_hash="x", full_name=name,
             normalized_full_name=name.lower(), organization_id=org_id, is_active=True)
    db.add(u)
    await db.flush()
    return u


async def _import(http, token, content, organization_id=None):
    data = {"organization_id": str(organization_id)} if organization_id else {}
    return await http.post(
        "/api/v1/admin/medical-exams/import", headers=auth(token), data=data,
        files={"file": ("med.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )


async def test_unique_name_is_linked(http, db):
    user = await _user(db, "Иванов Иван Иванович")
    _, token = await make_admin(db)
    await db.commit()

    resp = await _import(http, token, _file([[1, "Иванов Иван Иванович", date(1990, 1, 1), "Слесарь", "+", date(2026, 3, 1)]]))
    assert resp.status_code == 201, resp.text
    assert resp.json()["unmatched"] == []
    exam = (await db.execute(select(MedicalExam))).scalar_one()
    assert exam.user_id == user.id


async def test_namesakes_are_not_guessed(http, db):
    """Два «Ахметова Нурлана» — запись остаётся непривязанной для ручного выбора."""
    org_a = Organization(id=uuid4(), name="ТОО А", is_active=True)
    org_b = Organization(id=uuid4(), name="ТОО Б", is_active=True)
    db.add_all([org_a, org_b])
    await db.flush()
    await _user(db, "Ахметов Нурлан", org_a.id)
    await _user(db, "Ахметов Нурлан", org_b.id)
    _, token = await make_admin(db)
    await db.commit()

    resp = await _import(http, token, _file([[1, "Ахметов Нурлан", None, "Оператор", "+", date(2026, 3, 1)]]))
    assert resp.status_code == 201, resp.text
    assert len(resp.json()["unmatched"]) == 1
    exam = (await db.execute(select(MedicalExam))).scalar_one()
    assert exam.user_id is None


async def test_namesakes_resolved_by_selected_organization(http, db):
    org_a = Organization(id=uuid4(), name="ТОО А2", is_active=True)
    org_b = Organization(id=uuid4(), name="ТОО Б2", is_active=True)
    db.add_all([org_a, org_b])
    await db.flush()
    mine = await _user(db, "Ахметов Нурлан", org_a.id)
    await _user(db, "Ахметов Нурлан", org_b.id)
    _, token = await make_admin(db)
    await db.commit()

    resp = await _import(http, token, _file([[1, "Ахметов Нурлан", None, "Оператор", "+", date(2026, 3, 1)]]),
                         organization_id=org_a.id)
    assert resp.json()["unmatched"] == []
    exam = (await db.execute(select(MedicalExam))).scalar_one()
    assert exam.user_id == mine.id


async def test_reimport_same_file_does_not_duplicate(http, db):
    await _user(db, "Петров Пётр")
    _, token = await make_admin(db)
    await db.commit()
    content = _file([[1, "Петров Пётр", date(1985, 5, 5), "Мастер", "+", date(2026, 3, 1)]])

    first = await _import(http, token, content)
    second = await _import(http, token, content)
    assert first.json()["imported"] == 1
    assert second.json()["imported"] == 0 and second.json()["skipped_duplicates"] == 1
    count = (await db.execute(select(func.count()).select_from(MedicalExam))).scalar_one()
    assert count == 1
