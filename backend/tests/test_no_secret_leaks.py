"""
Регрессия: API не должен отдавать в браузер хеши паролей и внутренние пути.

Раньше /admin/users возвращал ORM-объекты целиком (с password_hash и
photo_path), а детали протокола — подгруженного AdminUser члена комиссии
(тоже с password_hash). Наблюдатель организации видел пароли сотрудников.
"""
from uuid import uuid4

from app.models.organization import Organization
from app.models.user import User
from app.models.protocol import CommissionRole
from tests.conftest import (
    make_admin, make_training_type, make_protocol, make_commission_member,
)

SECRETS = ("password_hash", "photo_path")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _org_with_user(db, name="Org Leak"):
    org = Organization(id=uuid4(), name=name, is_active=True)
    db.add(org)
    await db.flush()
    user = User(
        id=uuid4(), login=f"u_{uuid4().hex[:8]}", password_hash="SECRET-HASH",
        plain_password="Plain123", full_name="Сотрудник", normalized_full_name="сотрудник",
        organization_id=org.id, is_active=True, photo_path="/app/storage/photos/x.jpg",
    )
    db.add(user)
    await db.flush()
    return org, user


async def test_users_list_has_no_hash_or_disk_path(http, db):
    await _org_with_user(db)
    _, token = await make_admin(db)
    await db.commit()

    resp = await http.get("/api/v1/admin/users", headers=auth(token))
    assert resp.status_code == 200, resp.text
    for secret in SECRETS:
        assert secret not in resp.text
    row = resp.json()[0]
    assert row["plain_password"] == "Plain123"  # админ пароль видит — так задумано
    assert row["photo_url"].endswith("/photo")


async def test_org_viewer_does_not_get_employee_passwords(http, db):
    org, _ = await _org_with_user(db, "Org Viewer Pw")
    _, token = await make_admin(db, organization_id=org.id, is_org_viewer=True)
    await db.commit()

    resp = await http.get("/api/v1/admin/users", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert resp.json() and all(u["plain_password"] is None for u in resp.json())


async def test_org_viewer_lists_only_own_organization(http, db):
    org, _ = await _org_with_user(db, "Своя организация")
    await _org_with_user(db, "Чужая организация")
    _, token = await make_admin(db, organization_id=org.id, is_org_viewer=True)
    await db.commit()

    resp = await http.get("/api/v1/admin/organizations", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert [o["name"] for o in resp.json()] == ["Своя организация"]


async def test_protocol_detail_has_no_commission_password_hash(http, db):
    admin, token = await make_admin(db, is_superadmin=True)
    chair, _ = await make_admin(db, full_name="Председатель", is_commission_eligible=True)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, chair, role=CommissionRole.chair)
    await db.commit()

    resp = await http.get(f"/api/v1/admin/protocols/{protocol.id}", headers=auth(token))
    assert resp.status_code == 200, resp.text
    assert "password_hash" not in resp.text
    assert resp.json()["commission_members"][0]["full_name"] == "Председатель"
