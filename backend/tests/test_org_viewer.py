"""
Org-viewer role — a read-only admin account scoped to one organization.

Rules:
 1. Scoped lists (/admin/users) only return rows for the viewer's own
    organization, even if a different org_id is requested via query params.
 2. Org viewers are rejected (403) on write endpoints (reuses the same
    dependency every mutation already goes through).
"""
from uuid import uuid4
from app.models.user import User
from app.models.organization import Organization
from tests.conftest import make_admin


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _make_org(db, name):
    org = Organization(id=uuid4(), name=name, is_active=True)
    db.add(org)
    await db.flush()
    return org


async def _make_user(db, org_id, full_name):
    user = User(
        id=uuid4(), login=f"u_{uuid4().hex[:8]}", password_hash="x",
        full_name=full_name, normalized_full_name=full_name.lower(),
        organization_id=org_id, is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


async def test_org_viewer_only_sees_own_organization_users(http, db):
    org_a = await _make_org(db, "Org A")
    org_b = await _make_org(db, "Org B")
    await _make_user(db, org_a.id, "Сотрудник А")
    await _make_user(db, org_b.id, "Сотрудник Б")
    await db.commit()

    viewer, token = await make_admin(db, organization_id=org_a.id, is_org_viewer=True)
    await db.commit()

    resp = await http.get("/api/v1/admin/users", headers=auth(token))
    assert resp.status_code == 200, resp.text
    names = {u["full_name"] for u in resp.json()}
    assert names == {"Сотрудник А"}


async def test_org_viewer_cannot_override_scope_via_query_param(http, db):
    """A malicious/confused client passing organization_id=<other org> must
    not escape the viewer's own scope."""
    org_a = await _make_org(db, "Org A2")
    org_b = await _make_org(db, "Org B2")
    await _make_user(db, org_a.id, "Свой")
    await _make_user(db, org_b.id, "Чужой")
    await db.commit()

    viewer, token = await make_admin(db, organization_id=org_a.id, is_org_viewer=True)
    await db.commit()

    resp = await http.get(
        "/api/v1/admin/users",
        headers=auth(token),
        params={"organization_id": str(org_b.id)},
    )
    assert resp.status_code == 200, resp.text
    names = {u["full_name"] for u in resp.json()}
    assert names == {"Свой"}


async def test_org_viewer_rejected_on_write_endpoint(http, db):
    org = await _make_org(db, "Org C")
    viewer, token = await make_admin(db, organization_id=org.id, is_org_viewer=True)
    await db.commit()

    resp = await http.post(
        "/api/v1/admin/users",
        headers=auth(token),
        json={"full_name": "Новый сотрудник"},
    )
    assert resp.status_code == 403, resp.text


async def test_regular_admin_unaffected_sees_all_organizations(http, db):
    org_a = await _make_org(db, "Org D")
    org_b = await _make_org(db, "Org E")
    await _make_user(db, org_a.id, "Из D")
    await _make_user(db, org_b.id, "Из E")
    await db.commit()

    admin, token = await make_admin(db)
    await db.commit()

    resp = await http.get("/api/v1/admin/users", headers=auth(token))
    assert resp.status_code == 200, resp.text
    names = {u["full_name"] for u in resp.json()}
    assert {"Из D", "Из E"}.issubset(names)
