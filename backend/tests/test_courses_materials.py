"""
Курсы и материалы: удаление не оставляет файлы на диске и не падает 500,
если курс уже назначен сотрудникам.
"""
import os
from uuid import uuid4

from app.core.config import settings
from app.models.assignment import AssignmentStatus, UserCourseAssignment
from app.models.course import Course
from app.models.discipline import Discipline
from app.models.user import User
from tests.conftest import make_admin


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _course(db):
    disc = Discipline(id=uuid4(), code=f"D{uuid4().hex[:5]}", name="Дисциплина")
    db.add(disc)
    await db.flush()
    course = Course(id=uuid4(), discipline_id=disc.id, name="Курс", is_active=True)
    db.add(course)
    await db.flush()
    return disc, course


async def _upload(http, token, course_id, name="урок.pdf", content=b"%PDF-1.4 test"):
    return await http.post(
        f"/api/v1/admin/materials/courses/{course_id}", headers=auth(token),
        data={"title": "Материал", "material_type": "pdf"},
        files={"file": (name, content, "application/pdf")},
    )


async def test_material_upload_and_delete_removes_file(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    _, course = await _course(db)
    _, token = await make_admin(db)
    await db.commit()

    resp = await _upload(http, token, course.id)
    assert resp.status_code == 201, resp.text
    path = resp.json()["file_path"]
    assert os.path.isfile(path)
    assert resp.json()["file_size_bytes"] == len(b"%PDF-1.4 test")

    resp = await http.delete(f"/api/v1/admin/materials/{resp.json()['id']}", headers=auth(token))
    assert resp.status_code == 204
    assert not os.path.exists(path)


async def test_material_too_large_rejected_and_not_left_on_disk(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "MAX_MATERIAL_SIZE_MB", 1)
    _, course = await _course(db)
    _, token = await make_admin(db)
    await db.commit()

    resp = await _upload(http, token, course.id, content=b"x" * (2 * 1024 * 1024))
    assert resp.status_code == 413
    leftovers = [f for _, _, files in os.walk(tmp_path) for f in files]
    assert leftovers == []


async def test_material_for_missing_course_is_404(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    _, token = await make_admin(db)
    await db.commit()
    resp = await _upload(http, token, uuid4())
    assert resp.status_code == 404


async def test_cannot_delete_course_with_assignments(http, db):
    disc, course = await _course(db)
    user = User(id=uuid4(), login=f"u_{uuid4().hex[:6]}", password_hash="x", full_name="Сотрудник",
                normalized_full_name="сотрудник", is_active=True)
    db.add(user)
    await db.flush()
    db.add(UserCourseAssignment(user_id=user.id, course_id=course.id, discipline_id=disc.id,
                                status=AssignmentStatus.passed))
    _, token = await make_admin(db)
    await db.commit()

    resp = await http.delete(f"/api/v1/admin/courses/{course.id}", headers=auth(token))
    assert resp.status_code == 409, resp.text
    assert "Активен" in resp.json()["detail"]


async def test_delete_unassigned_course_removes_material_files(http, db, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "STORAGE_LOCAL_PATH", str(tmp_path))
    _, course = await _course(db)
    _, token = await make_admin(db)
    await db.commit()
    path = (await _upload(http, token, course.id)).json()["file_path"]

    resp = await http.delete(f"/api/v1/admin/courses/{course.id}", headers=auth(token))
    assert resp.status_code == 204, resp.text
    assert not os.path.exists(path)
