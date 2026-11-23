"""
Списки админки отдаются постранично с общим количеством в X-Total-Count.

Раньше они молча обрезались (удостоверения/протоколы — 50, пользователи и
прогресс — 500): на проде было видно 50 из 910 удостоверений, а поиск
протокола по номеру искал только среди загруженных 50.
"""
from datetime import date, timedelta
from uuid import uuid4

from app.models.certificate import Certificate
from app.models.organization import Organization
from app.models.protocol import Protocol
from app.models.user import User
from tests.conftest import make_admin, make_training_type


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def test_certificates_paged_with_total(http, db):
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    for i in range(7):
        db.add(Certificate(id=uuid4(), certificate_number=f"PG-{i:03d}", training_type_id=tt.id,
                           full_name=f"Сотрудник {i}", issued_date=date(2026, 1, 1) + timedelta(days=i)))
    await db.commit()

    page1 = await http.get("/api/v1/admin/certificates", headers=auth(token), params={"limit": 3})
    assert page1.status_code == 200, page1.text
    assert page1.headers["x-total-count"] == "7"
    assert len(page1.json()) == 3
    page3 = await http.get("/api/v1/admin/certificates", headers=auth(token), params={"limit": 3, "skip": 6})
    assert len(page3.json()) == 1
    # Страницы не пересекаются
    ids = {c["id"] for c in page1.json()} | {c["id"] for c in page3.json()}
    assert len(ids) == 4


async def test_certificate_search_by_number(http, db):
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    db.add(Certificate(id=uuid4(), certificate_number="БИОТ-20260101-0042", training_type_id=tt.id,
                       full_name="Иванов", issued_date=date(2026, 1, 1)))
    await db.commit()
    resp = await http.get("/api/v1/admin/certificates", headers=auth(token), params={"search": "0042"})
    assert [c["full_name"] for c in resp.json()] == ["Иванов"]


async def test_protocols_server_search_finds_old_ones(http, db):
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    org = Organization(id=uuid4(), name="ТОО Старая Организация", is_active=True)
    db.add(org)
    await db.flush()
    for i in range(60):
        db.add(Protocol(id=uuid4(), protocol_number=f"N-{i:03d}", training_type_id=tt.id,
                        exam_date=date(2025, 1, 1) + timedelta(days=i),
                        organization_id=org.id if i == 0 else None))
    await db.commit()

    first_page = await http.get("/api/v1/admin/protocols", headers=auth(token))
    assert first_page.headers["x-total-count"] == "60"
    assert "N-000" not in {p["protocol_number"] for p in first_page.json()}  # самый старый — не на 1-й странице

    by_number = await http.get("/api/v1/admin/protocols", headers=auth(token), params={"search": "N-000"})
    assert [p["protocol_number"] for p in by_number.json()] == ["N-000"]
    by_org = await http.get("/api/v1/admin/protocols", headers=auth(token), params={"search": "старая"})
    assert [p["protocol_number"] for p in by_org.json()] == ["N-000"]


async def test_users_total_count_header(http, db):
    admin, token = await make_admin(db)
    for i in range(5):
        db.add(User(id=uuid4(), login=f"pg_{i}_{uuid4().hex[:4]}", password_hash="x",
                    full_name=f"Пользователь {i}", normalized_full_name=f"пользователь {i}", is_active=True))
    await db.commit()
    resp = await http.get("/api/v1/admin/users", headers=auth(token), params={"limit": 2})
    assert resp.headers["x-total-count"] == "5"
    assert len(resp.json()) == 2


async def test_limit_is_capped(http, db):
    admin, token = await make_admin(db)
    await db.commit()
    resp = await http.get("/api/v1/admin/certificates", headers=auth(token), params={"limit": 10**9})
    assert resp.status_code == 200
