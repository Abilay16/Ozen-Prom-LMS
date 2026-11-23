"""
Импорт сотрудников из Excel: разбор реальных вариантов файлов и создание
пользователей без склейки с однофамильцами.
"""
import os
import tempfile
from uuid import uuid4

import openpyxl
from sqlalchemy import select

from app.core.config import settings
from app.models.batch import BatchStatus, TrainingBatch
from app.models.course import Course
from app.models.discipline import Discipline
from app.models.organization import Organization
from app.models.user import User
from app.services.imports.parser import ImportParserService
from tests.conftest import make_admin


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def _xlsx(rows) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    wb.save(path)
    return path


# ── Разбор файла ────────────────────────────────────────────────────────────

def test_parser_title_rows_above_table():
    path = _xlsx([
        ["Список сотрудников ТОО «Пример» на обучение"],
        [],
        ["№", "ФИО", "Должность", "Организация"],
        [1, "Иванов Иван Иванович", "Слесарь", "ТОО Пример"],
        [2, "Петров Пётр", "Мастер", "ТОО Пример"],
    ])
    preview = ImportParserService().parse_preview(path)
    assert "parse_error" not in preview
    assert [r["full_name"] for r in preview["rows"]] == ["Иванов Иван Иванович", "Петров Пётр"]
    assert preview["rows"][0]["row_number"] == 4  # реальный номер строки в Excel
    assert preview["rows"][0]["position"] == "Слесарь"


def test_parser_split_name_columns():
    path = _xlsx([
        ["Фамилия", "Имя", "Отчество", "Должность"],
        ["Ахметов", "Нурлан", "Серикович", "Оператор"],
        ["Ким", "Ольга", "", "Инженер"],
    ])
    preview = ImportParserService().parse_preview(path)
    assert [r["full_name"] for r in preview["rows"]] == ["Ахметов Нурлан Серикович", "Ким Ольга"]


def test_parser_short_header_does_not_hijack_column():
    """Заголовок «П» раньше совпадал с частью слова «предприятие»."""
    path = _xlsx([
        ["П", "Ф.И.О.", "Должность", "Предприятие"],
        ["1", "Сидоров С.С.", "Водитель", "ТОО Транс"],
    ])
    row = ImportParserService().parse_preview(path)["rows"][0]
    assert row["full_name"] == "Сидоров С.С."
    assert row["organization"] == "ТОО Транс"


def test_parser_skips_blank_rows_and_collapses_spaces():
    path = _xlsx([
        ["ФИО", "Должность"],
        ["  Иванов   Иван ", "Слесарь"],
        [None, None],
        ["", ""],
        ["Петров Пётр", "Мастер"],
    ])
    preview = ImportParserService().parse_preview(path)
    assert [r["full_name"] for r in preview["rows"]] == ["Иванов Иван", "Петров Пётр"]
    assert preview["error"] == 0


def test_parser_reports_missing_name_column():
    path = _xlsx([["Колонка1", "Колонка2"], ["a", "b"]])
    preview = ImportParserService().parse_preview(path)
    assert "ФИО" in preview["parse_error"]


# ── Импорт ──────────────────────────────────────────────────────────────────

async def _batch_with_course(db, organization_id=None):
    disc = Discipline(id=uuid4(), code=f"D{uuid4().hex[:5]}", name="БиОТ")
    db.add(disc)
    await db.flush()
    db.add(Course(id=uuid4(), discipline_id=disc.id, name="Курс для всех", is_active=True))
    batch = TrainingBatch(id=uuid4(), name="Поток", discipline_ids=[str(disc.id)],
                          organization_id=organization_id, status=BatchStatus.processing)
    db.add(batch)
    await db.flush()
    return batch


async def _upload(http, token, batch, rows):
    path = _xlsx(rows)
    with open(path, "rb") as f:
        resp = await http.post(f"/api/v1/admin/batches/{batch.id}/upload-excel", headers=auth(token),
                               files={"file": ("сотрудники.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert resp.status_code == 200, resp.text


async def test_import_without_org_does_not_merge_with_namesake_from_other_company(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    other = Organization(id=uuid4(), name="ТОО Чужая", is_active=True)
    db.add(other)
    await db.flush()
    namesake = User(id=uuid4(), login="namesake", password_hash="x", full_name="Ахметов Нурлан",
                    normalized_full_name="ахметов нурлан", organization_id=other.id, is_active=True)
    db.add(namesake)
    batch = await _batch_with_course(db)
    _, token = await make_admin(db)
    await db.commit()

    await _upload(http, token, batch, [["ФИО", "Должность"], ["Ахметов Нурлан", "Слесарь"]])
    resp = await http.post(f"/api/v1/admin/batches/{batch.id}/confirm-import", headers=auth(token))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["summary"]["created"] == 1 and body["summary"]["duplicates"] == 0
    assert body["credentials"][0]["login"] != "namesake"


async def test_import_uses_batch_organization_when_row_has_none(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    org = Organization(id=uuid4(), name="ТОО Поток", is_active=True)
    db.add(org)
    await db.flush()
    batch = await _batch_with_course(db, organization_id=org.id)
    _, token = await make_admin(db)
    await db.commit()

    await _upload(http, token, batch, [["ФИО", "Должность"], ["Новиков Олег", "Слесарь"]])
    resp = await http.post(f"/api/v1/admin/batches/{batch.id}/confirm-import", headers=auth(token))
    assert resp.status_code == 200, resp.text
    user = (await db.execute(select(User).where(User.normalized_full_name == "новиков олег"))).scalar_one()
    assert user.organization_id == org.id


async def test_existing_org_matched_case_insensitively(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    org = Organization(id=uuid4(), name="ТОО КазМунайСервис", is_active=True)
    db.add(org)
    batch = await _batch_with_course(db)
    _, token = await make_admin(db)
    await db.commit()

    await _upload(http, token, batch, [["ФИО", "Должность", "Организация"], ["Ким Ольга", "Инженер", "  тоо   казмунайсервис "]])
    await http.post(f"/api/v1/admin/batches/{batch.id}/confirm-import", headers=auth(token))
    orgs = (await db.execute(select(Organization).where(Organization.name.ilike("%казмунай%")))).scalars().all()
    assert len(orgs) == 1


async def test_confirm_import_twice_is_rejected(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    batch = await _batch_with_course(db)
    _, token = await make_admin(db)
    await db.commit()

    await _upload(http, token, batch, [["ФИО", "Должность"], ["Орлов Игорь", "Слесарь"]])
    first = await http.post(f"/api/v1/admin/batches/{batch.id}/confirm-import", headers=auth(token))
    assert first.status_code == 200 and first.json()["credentials"]
    second = await http.post(f"/api/v1/admin/batches/{batch.id}/confirm-import", headers=auth(token))
    assert second.status_code == 409, second.text


async def test_confirm_import_without_name_column_is_422(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    batch = await _batch_with_course(db)
    _, token = await make_admin(db)
    await db.commit()

    await _upload(http, token, batch, [["Что-то", "Ещё"], ["a", "b"]])
    resp = await http.post(f"/api/v1/admin/batches/{batch.id}/confirm-import", headers=auth(token))
    assert resp.status_code == 422
    assert "ФИО" in resp.json()["detail"]


async def test_manual_add_saves_password_for_admin_view(http, db):
    batch = await _batch_with_course(db)
    _, token = await make_admin(db)
    await db.commit()

    resp = await http.post(f"/api/v1/admin/batches/{batch.id}/add-user", headers=auth(token),
                           json={"full_name": "Ручной   Сотрудник", "position": "Слесарь"})
    assert resp.status_code == 201, resp.text
    user = (await db.execute(select(User).where(User.login == resp.json()["login"]))).scalar_one()
    assert user.plain_password == resp.json()["password"]
    assert user.full_name == "Ручной Сотрудник"
