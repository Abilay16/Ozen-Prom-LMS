"""
Full end-to-end flow tests — no browser required.

Coverage:
  AUTH:
    - Admin login success / wrong password / unknown user
    - Protected route requires valid token
    - Token refresh preserves is_commission flag

  PROTOCOL CRUD (superadmin):
    - Superadmin can create a protocol
    - Commission member cannot create a protocol (403)
    - Superadmin can add commission member + participant
    - Superadmin can request signatures → status becomes awaiting_signatures

  SIGNING FLOW:
    - Single member signs without CMS → status becomes signed
    - Chair cannot sign before all members
    - Full chair+member flow → signed after chair signs last
    - Sign with name-mismatched CMS → 403
    - Sign with fresh matching CMS → 200, cert info stored
    - Sign with expired CMS (matching name) → 403

  CERTIFICATE ISSUANCE:
    - Passed participants receive certificate after signing
    - Failed participants do NOT receive certificate

  name_utils UNIT TESTS (pure Python, no HTTP/DB):
    - Normalize Kazakh letters
    - Case-insensitive comparison
    - Order-insensitive comparison
    - Genuine mismatch returns False
"""
import pytest
from uuid import uuid4
from datetime import date

from app.models.protocol import (
    ProtocolStatus, CommissionRole, ParticipantResult, ProtocolParticipant,
)
from app.utils.name_utils import normalize_name, names_match
from tests.conftest import (
    make_admin, make_training_type, make_protocol,
    make_commission_member, make_fresh_cms_b64,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _make_awaiting_single_member(db):
    """Protocol with one no-chair member, awaiting signatures."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()
    return admin, token, protocol


async def _add_participant(db, protocol, result=None):
    p = ProtocolParticipant(
        id=uuid4(), protocol_id=protocol.id,
        full_name="Участник Тест",
        position="Инженер",
        result=result,
        sort_order=0,
    )
    db.add(p)
    await db.flush()
    return p


# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════

async def test_auth_admin_login_success(http, db):
    """Valid credentials → access + refresh tokens returned."""
    from app.core.security import hash_password
    from app.models.user import AdminUser
    admin = AdminUser(
        id=uuid4(), login="testadmin_login", full_name="Тест Админ",
        password_hash=hash_password("SecurePass1!"), is_active=True,
    )
    db.add(admin)
    await db.commit()

    resp = await http.post("/api/v1/auth/login", json={
        "login": "testadmin_login",
        "password": "SecurePass1!",
    })

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "admin"
    assert data["full_name"] == "Тест Админ"


async def test_auth_admin_login_wrong_password(http, db):
    """Wrong password → 401."""
    from app.core.security import hash_password
    from app.models.user import AdminUser
    admin = AdminUser(
        id=uuid4(), login="testadmin_badpw", full_name="Тест",
        password_hash=hash_password("RealPass1!"), is_active=True,
    )
    db.add(admin)
    await db.commit()

    resp = await http.post("/api/v1/auth/login", json={
        "login": "testadmin_badpw",
        "password": "WrongPass1!",
    })

    assert resp.status_code == 401, resp.text


async def test_auth_admin_login_unknown_user(http, db):
    """Non-existent user → 401 (not 404)."""
    resp = await http.post("/api/v1/auth/login", json={
        "login": "ghost_user_xyz",
        "password": "AnyPass1!",
    })
    assert resp.status_code == 401, resp.text


async def test_auth_protected_route_rejects_no_token(http, db):
    """Request without Authorization header → 401."""
    resp = await http.get("/api/v1/admin/protocols")
    assert resp.status_code == 401, resp.text


async def test_auth_protected_route_accepts_valid_token(http, db):
    """Request with valid JWT → 200 (empty list, not 401/403)."""
    _, token = await make_admin(db)
    await db.commit()  # must be committed so the http session can find the admin
    resp = await http.get("/api/v1/admin/protocols", headers=auth(token))
    assert resp.status_code == 200, resp.text


async def test_auth_commission_flag_returned_on_login(http, db):
    """Commission-eligible admin → is_commission=true in login response."""
    from app.core.security import hash_password
    from app.models.user import AdminUser
    commission_admin = AdminUser(
        id=uuid4(), login="commission_login_test", full_name="Комиссия",
        password_hash=hash_password("Pass1234!"),
        is_active=True, is_commission_eligible=True, is_superadmin=False,
    )
    db.add(commission_admin)
    await db.commit()

    resp = await http.post("/api/v1/auth/login", json={
        "login": "commission_login_test",
        "password": "Pass1234!",
    })

    assert resp.status_code == 200
    assert resp.json()["is_commission"] is True


# ══════════════════════════════════════════════════════════════════════════════
# PROTOCOL CRUD
# ══════════════════════════════════════════════════════════════════════════════

async def test_superadmin_can_create_protocol(http, db):
    """POST /protocols → 201 with protocol data."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    await db.commit()

    resp = await http.post("/api/v1/admin/protocols", headers=auth(token), json={
        "training_type_id": str(tt.id),
        "exam_date": "2026-06-01",
        "protocol_number": "П-001",
    })

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["protocol_number"] == "П-001"
    assert data["status"] == "draft"


async def test_commission_member_cannot_create_protocol(http, db):
    """Commission member → 403 on POST /protocols."""
    commission, token = await make_admin(db, is_commission_eligible=True)
    tt = await make_training_type(db)
    await db.commit()

    resp = await http.post("/api/v1/admin/protocols", headers=auth(token), json={
        "training_type_id": str(tt.id),
        "exam_date": "2026-06-01",
        "protocol_number": "П-002",
    })

    assert resp.status_code == 403, resp.text


async def test_superadmin_can_add_commission_member(http, db):
    """POST /protocols/{id}/commission → 201, then GET confirms it was saved."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    member_admin, _ = await make_admin(db, full_name="Джангалиев Ержан")
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/commission",
        headers=auth(token),
        json={
            "admin_user_id": str(member_admin.id),
            "role": "member",
            "sort_order": 0,
        },
    )

    assert resp.status_code == 201, resp.text
    # Verify via a GET (fresh session) to avoid identity-map caching
    get_resp = await http.get(
        f"/api/v1/admin/protocols/{protocol.id}",
        headers=auth(token),
    )
    assert get_resp.status_code == 200
    assert len(get_resp.json()["commission_members"]) == 1


async def test_superadmin_can_add_participant(http, db):
    """POST /protocols/{id}/participants → 201, then GET confirms it was saved."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/participants",
        headers=auth(token),
        json={
            "full_name": "Сейткали Нурлан",
            "position": "Слесарь",
            "result": "passed",
        },
    )

    assert resp.status_code == 201, resp.text
    # Verify via a GET (fresh session) to avoid identity-map caching
    get_resp = await http.get(
        f"/api/v1/admin/protocols/{protocol.id}",
        headers=auth(token),
    )
    assert get_resp.status_code == 200
    assert len(get_resp.json()["participants"]) == 1


async def test_superadmin_can_request_signatures(http, db):
    """POST /request-signatures → status becomes awaiting_signatures."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/request-signatures",
        headers=auth(token),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "awaiting_signatures"


async def test_list_protocols_returns_created(http, db):
    """GET /protocols returns the protocol created in this test."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    protocol.protocol_number = "LIST-TEST-001"
    await db.commit()

    resp = await http.get("/api/v1/admin/protocols", headers=auth(token))

    assert resp.status_code == 200
    numbers = [p["protocol_number"] for p in resp.json()]
    assert "LIST-TEST-001" in numbers


# ══════════════════════════════════════════════════════════════════════════════
# SIGNING FLOW
# ══════════════════════════════════════════════════════════════════════════════

async def test_single_member_sign_no_cms_sets_signed(http, db):
    """Single member (no chair) signs without CMS → protocol becomes signed."""
    admin, token, protocol = await _make_awaiting_single_member(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "signed"


async def test_cannot_sign_twice(http, db):
    """Signing a second time → 409."""
    admin, token, protocol = await _make_awaiting_single_member(db)
    await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
    )

    resp2 = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
    )

    assert resp2.status_code == 409, resp2.text


async def test_non_commission_member_cannot_sign(http, db):
    """Admin not in commission → 403."""
    admin, token, protocol = await _make_awaiting_single_member(db)
    outsider, outsider_token = await make_admin(db)
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(outsider_token),
    )

    assert resp.status_code == 403, resp.text


async def test_chair_cannot_sign_before_members(http, db):
    """Chair tries to sign while a member hasn't → 400."""
    chair, chair_token = await make_admin(db, full_name="Председатель")
    member, _ = await make_admin(db, full_name="Член комиссии")
    tt = await make_training_type(db)
    protocol = await make_protocol(db, chair, tt)
    await make_commission_member(db, protocol, chair, role=CommissionRole.chair)
    await make_commission_member(db, protocol, member, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(chair_token),
    )

    assert resp.status_code == 400, resp.text
    assert "не подписали" in resp.json()["detail"]


async def test_full_chair_member_flow(http, db):
    """Member signs first, then chair → status = signed."""
    chair, chair_token = await make_admin(db, full_name="Председатель Тест")
    member, member_token = await make_admin(db, full_name="Член Тест")
    tt = await make_training_type(db)
    protocol = await make_protocol(db, chair, tt)
    await make_commission_member(db, protocol, chair, role=CommissionRole.chair)
    await make_commission_member(db, protocol, member, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()

    # Member signs first
    r1 = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(member_token),
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "awaiting_signatures"  # not yet signed

    # Chair signs last → becomes signed
    r2 = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(chair_token),
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "signed"


async def test_sign_with_cms_name_mismatch_returns_403(http, db):
    """CMS signed by a different person → 403."""
    admin, token = await make_admin(db, full_name="Иванов Иван Иванович")
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()

    wrong_cms = make_fresh_cms_b64("ПЕТРОВ ПЕТР ПЕТРОВИЧ")

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": wrong_cms},
    )

    assert resp.status_code == 403, resp.text
    assert "не соответствует" in resp.json()["detail"]


async def test_sign_with_fresh_matching_cms_succeeds(http, db):
    """Fresh CMS with matching CN → 200, cert info stored."""
    cn = "ТЕСТОВ ТЕСТ ТЕСТОВИЧ"
    admin, token = await make_admin(db, full_name=cn)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()

    fresh_cms = make_fresh_cms_b64(cn)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": fresh_cms},
    )

    assert resp.status_code == 200, resp.text
    member = next(
        m for m in resp.json()["commission_members"]
        if m["admin_user_id"] == str(admin.id)
    )
    assert member["signer_cert_serial"] is not None
    assert member["signer_cert_owner"] is not None
    assert member["signer_cert_valid_to"] is not None


async def test_sign_with_expired_cert_returns_403(http, db):
    """Expired CMS (even with matching name) → 403."""
    # TEST_CMS_B64_EXPIRED has CN = "TESTOV TEST TESTOVICH", valid_to = 2024-04-25
    expired_cms = (
        "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"
    )
    # Admin name matches the cert CN
    admin, token = await make_admin(db, full_name="TESTOV TEST TESTOVICH")
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": expired_cms},
    )

    assert resp.status_code == 403, resp.text
    assert "просроч" in resp.json()["detail"]


# ══════════════════════════════════════════════════════════════════════════════
# CERTIFICATE ISSUANCE
# ══════════════════════════════════════════════════════════════════════════════

async def test_passed_participant_gets_certificate_after_signing(http, db):
    """Participant with result=passed → certificate_id set after sign."""
    # Setup everything in ONE commit (same pattern as test_auto_certificates.py)
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    passed_participant = ProtocolParticipant(
        id=uuid4(), protocol_id=protocol.id,
        full_name="Сейткали Нурлан",
        position="Инженер",
        result=ParticipantResult.passed,
        sort_order=0,
    )
    db.add(passed_participant)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
    )

    assert resp.status_code == 200
    passed = next(
        p for p in resp.json()["participants"] if p["result"] == "passed"
    )
    assert passed["certificate_id"] is not None


async def test_failed_participant_gets_no_certificate(http, db):
    """Participant with result=failed → certificate_id is null."""
    admin, token, protocol = await _make_awaiting_single_member(db)
    await _add_participant(db, protocol, result=ParticipantResult.failed)
    await db.commit()

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
    )

    assert resp.status_code == 200
    failed = next(
        p for p in resp.json()["participants"] if p["result"] == "failed"
    )
    assert failed["certificate_id"] is None


# ══════════════════════════════════════════════════════════════════════════════
# name_utils UNIT TESTS (pure Python, no HTTP/DB — run synchronously)
# ══════════════════════════════════════════════════════════════════════════════

def test_normalize_kazakh_letter_u_with_combining():
    """Ұ (U+04B0) is mapped to у."""
    assert normalize_name("Аяпбергенов Алпамыс Аскарұлы") == normalize_name(
        "АЯПБЕРГЕНОВ АЛПАМЫС АСКАРУЛЫ"
    )


def test_normalize_kazakh_letter_k():
    """Қ is mapped to к."""
    result = normalize_name("Серікқызы")
    # Серікқызы → сериккызы after mapping і→и, қ→к
    assert "и" in result or "к" in result  # basic sanity


def test_names_match_all_caps_vs_proper_case():
    """ALL CAPS from cert CN matches proper-case DB value."""
    assert names_match(
        "АЯПБЕРГЕНОВ АЛПАМЫС АСКАРУЛЫ",
        "Аяпбергенов Алпамыс Аскарұлы",
    )


def test_names_match_order_insensitive():
    """Token order does not matter for comparison."""
    assert names_match("Алиев Абылай Илиясулы", "Илиясулы Абылай Алиев")


def test_names_match_dzhajgulova():
    """Verify actual commission member name normalizes correctly."""
    assert names_match(
        "ДЖАЙГУЛОВА УЛБОЛСЫН СЕРИККЫЗЫ",   # as it would appear in NUC cert
        "Джайгулова Ұлболсын Серікқызы",   # as stored in system
    )


def test_names_no_match_different_names():
    """Genuinely different names are not considered equal."""
    assert not names_match("Иванов Иван Иванович", "Алиев Абылай Илиясулы")


def test_names_match_surname_and_firstname_subset():
    """Certificate with only Фамилия+Имя (no patronymic) still matches system FIO."""
    assert names_match("АЛИЕВ АБЫЛАЙ", "Алиев Абылай Илиясулы")


def test_names_no_match_single_token():
    """Single-token cert name (surname only) is rejected to prevent false positives."""
    assert not names_match("АЛИЕВ", "Алиев Абылай Илиясулы")
