"""
Статус протокола меняется только по правилам: черновик → на подпись
(request-signatures) → подписан (подписью комиссии с ЭЦП) → архив.

Раньше PATCH принимал любой статус: можно было выставить «подписан» прямо
из черновика и выдать удостоверения без единой подписи комиссии.
"""
from app.models.protocol import ProtocolStatus
from tests.conftest import make_admin, make_training_type, make_protocol


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _protocol(db, status=ProtocolStatus.draft):
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    protocol.status = status
    await db.commit()
    return protocol, token


async def test_cannot_mark_draft_as_signed_via_patch(http, db):
    protocol, token = await _protocol(db)
    resp = await http.patch(f"/api/v1/admin/protocols/{protocol.id}", headers=auth(token), json={"status": "signed"})
    assert resp.status_code == 409, resp.text
    await db.refresh(protocol)
    assert protocol.status == ProtocolStatus.draft


async def test_cannot_mark_awaiting_as_signed_via_patch(http, db):
    protocol, token = await _protocol(db, ProtocolStatus.awaiting_signatures)
    resp = await http.patch(f"/api/v1/admin/protocols/{protocol.id}", headers=auth(token), json={"status": "signed"})
    assert resp.status_code == 409, resp.text


async def test_cannot_issue_certificates_for_unsigned_protocol(http, db):
    protocol, token = await _protocol(db, ProtocolStatus.awaiting_signatures)
    resp = await http.post(f"/api/v1/admin/protocols/{protocol.id}/issue-certificates", headers=auth(token))
    assert resp.status_code == 400, resp.text


async def test_signed_protocol_can_be_archived(http, db):
    protocol, token = await _protocol(db, ProtocolStatus.signed)
    resp = await http.patch(f"/api/v1/admin/protocols/{protocol.id}", headers=auth(token), json={"status": "archived"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "archived"


async def test_draft_fields_still_editable(http, db):
    protocol, token = await _protocol(db)
    resp = await http.patch(f"/api/v1/admin/protocols/{protocol.id}", headers=auth(token),
                            json={"protocol_number": "П-777"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["protocol_number"] == "П-777"
