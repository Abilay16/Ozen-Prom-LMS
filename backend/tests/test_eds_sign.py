"""
Backend EDS tests — Priority 2.

Tests for:
  1. GET  /protocols/{id}/signature-payload  → returns deterministic payload string
  2. POST /protocols/{id}/sign  (with CMS body) → stores cert info, sets signed_at
  3. POST /protocols/{id}/sign  (without CMS)   → backward compat, still works
  4. After signing, commission member response includes cert info fields
"""
import pytest
from datetime import datetime, timezone
from app.models.protocol import ProtocolStatus, CommissionRole, ParticipantResult
from tests.conftest import (
    make_admin, make_training_type, make_protocol, make_commission_member,
    make_fresh_cms_b64,
)

# CN used in all CMS-based signing tests
_TEST_CMS_CN = "TESTOV TEST TESTOVICH"

# Fresh self-signed CMS valid for 10 years — generated once per session at import time.
# Admin full_name must equal _TEST_CMS_CN so name-match check passes.
TEST_CMS_B64 = make_fresh_cms_b64(_TEST_CMS_CN)

# Original expired CMS (valid_to = 2024-04-25) — used only for expiry-check test.
TEST_CMS_B64_EXPIRED = (
    "MIIFPQYJKoZIhvcNAQcCoIIFLjCCBSoCAQExDzANBglghkgBZQMEAgEFADAkBgkqhkiG9w0BBwGg"
    "FwQVUFJPVE9DT0wgVEVTVCBQQVlMT0FEoIIC3zCCAtswggHDoAMCAQICCXDotlYAAQBCfzANBgkq"
    "hkiG9w0BAQsFADAtMQswCQYDVQQGEwJLWjEeMBwGA1UEAwwVVEVTVE9WIFRFU1QgVEVTVE9WSUNI"
    "MB4XDTIzMDEyNTAwMDAwMFoXDTI0MDQyNTAwMDAwMFowLTELMAkGA1UEBhMCS1oxHjAcBgNVBAMM"
    "FVRFU1RPViBURVNUIFRFU1RPVklDSDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMCJ"
    "m4UnAhRmbgWjAP7F8whpGC4y7Mr+RSB5z2wz+cLWj10uGvXwd5uA79BINN9aJMyl4C2FSMVGIIUh"
    "vCtZNvf5KLCkAKgHa4kIzXUF+ZETc/iEMSbYivYiC0Qs0vkojOM1LjfRYfqB2oNDIg6JCdSkzbR8"
    "uJU+xNya6zILQN3Yp62Hvoh54TF+FODxu58dHI33noWtzJ11t4EhF1FXw9mUXJ1RiXi+cSUD4RJE"
    "FVhHcWUFxHIysj+uBTHxK3eL2IEo8u/DDfQj61XdrMlZ986bgdlQkTjX9oeR5j0yStpKFMfSDe5c"
    "3y8I5IxD0c5qbVb00zTD4SWVXEskQbU38ZcCAwEAATANBgkqhkiG9w0BAQsFAAOCAQEAaGfmxBcG"
    "mfZyEDwwizT+bg6ShgZrjkpcMv8kkoqADE3g2/2LAHO5ICF+RTo6nQlWZ0heWqRlZSvc8VX4Ibl1"
    "Pwy2eWqam9HlXzU2rAKbKt8srBuo+5rmSUQkTuPqCLYVCcqJkHmMYUq7fNqxZEKcTqxGj5mCmW9q"
    "5MrS+wYcu/Dqzn0ULy/iU/6NYqVyYAMYpl35uu6CZsO/H6AzXLOcYlyS4MUUVdhAHHRWRwa5QOK3"
    "Ad4VuEUd8gLh8B0w0c2nubGGlL0z7XaRBcSzF24sSi2ffKux3uiGXQdQFXUaHMpl5V5sjToF2Vo6"
    "JNHSQwsHwrMsBy7fcDYG2PNskSkaNzGCAgkwggIFAgEBMDowLTELMAkGA1UEBhMCS1oxHjAcBgNV"
    "BAMMFVRFU1RPViBURVNUIFRFU1RPVklDSAIJcOi2VgABAEJ/MA0GCWCGSAFlAwQCAQUAoIGhMBgG"
    "CSqGSIb3DQEJAzELBgkqhkiG9w0BBwEwHAYJKoZIhvcNAQkFMQ8XDTI2MDUwNDEyNDUwNFowLwYJ"
    "KoZIhvcNAQkEMSIEIJR7mG4mgkHA+tszD8xzpiPwcN5+T9MBHON4K941XrVtMDYGCSqGSIb3DQEJ"
    "DzEpMCcwCwYJYIZIAWUDBAEqMAsGCWCGSAFlAwQBFjALBglghkgBZQMEAQIwDQYJKoZIhvcNAQEB"
    "BQAEggEAm8S9UfJXkAjpVLWOJiG4lVbnuLtAs642OL+1At91vKURkIQMHM1cX26oMlBttL4Nhllw"
    "n6Uukw18cdWvaqNEFoBEPMW+31bxKZZX5D+MR9sLa/sVuN4u5VylygNZkV+gaWv9zWjB1+HB0doo"
    "XUooceF1thDWNxsLwO9vaJUyTHjrTbjUwyhlJalC7XgTvV7p3kgtui4wv+gYpzn0a1gO5cESrps+"
    "BzcZuYXx0P0Btz5sf+4Naq5oCjHU4sTc014E1PkaiIpaHfA0IvM1eQyrMxX4aZClBWgOm1Mrd3YC"
    "HjSa3NxnOwa+4pBIXInh1eayQbJHVSmUvFWG7qxfN7yKGQ=="
)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _protocol_awaiting(db):
    """A protocol with one member-only commission, status = awaiting_signatures."""
    # full_name must match _TEST_CMS_CN so the name-check in sign_protocol passes
    admin, token = await make_admin(db, full_name=_TEST_CMS_CN)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt, batch=None)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()
    return admin, token, protocol


# ── 1. signature-payload ──────────────────────────────────────────────────────

async def test_signature_payload_returns_payload_field(http, db):
    """GET /signature-payload should return a non-empty payload string."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.get(
        f"/api/v1/admin/protocols/{protocol.id}/signature-payload",
        headers=auth(token),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "payload" in data
    assert len(data["payload"]) > 10


async def test_signature_payload_is_deterministic(http, db):
    """Calling /signature-payload twice returns the same string."""
    admin, token, protocol = await _protocol_awaiting(db)

    r1 = await http.get(
        f"/api/v1/admin/protocols/{protocol.id}/signature-payload",
        headers=auth(token),
    )
    r2 = await http.get(
        f"/api/v1/admin/protocols/{protocol.id}/signature-payload",
        headers=auth(token),
    )

    assert r1.json()["payload"] == r2.json()["payload"]


async def test_signature_payload_contains_protocol_number(http, db):
    """The payload string must embed the protocol number so its tied to this document."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.get(
        f"/api/v1/admin/protocols/{protocol.id}/signature-payload",
        headers=auth(token),
    )

    assert protocol.protocol_number in resp.json()["payload"]


# ── 2. sign with CMS ──────────────────────────────────────────────────────────

async def test_sign_with_cms_stores_cert_serial(http, db):
    """After signing with CMS, signer_cert_serial must be present in response."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": TEST_CMS_B64},
    )

    assert resp.status_code == 200, resp.text
    member = next(
        m for m in resp.json()["commission_members"]
        if m["admin_user_id"] == str(admin.id)
    )
    assert member["signer_cert_serial"] is not None
    assert len(member["signer_cert_serial"]) > 0


async def test_sign_with_cms_stores_cert_owner(http, db):
    """signer_cert_owner must contain the CN from the certificate."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": TEST_CMS_B64},
    )

    member = next(
        m for m in resp.json()["commission_members"]
        if m["admin_user_id"] == str(admin.id)
    )
    assert member["signer_cert_owner"] is not None
    # Our test cert CN is "TESTOV TEST TESTOVICH"
    assert "TESTOV" in member["signer_cert_owner"]


async def test_sign_with_cms_stores_validity_dates(http, db):
    """signer_cert_valid_from and signer_cert_valid_to must be populated."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": TEST_CMS_B64},
    )

    member = next(
        m for m in resp.json()["commission_members"]
        if m["admin_user_id"] == str(admin.id)
    )
    assert member["signer_cert_valid_from"] is not None
    assert member["signer_cert_valid_to"] is not None


# ── 3. sign WITHOUT cms (backward compat) ─────────────────────────────────────

async def test_sign_without_cms_still_works(http, db):
    """Signing without a CMS body must still transition the protocol correctly."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        # No JSON body at all
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "signed"


async def test_sign_without_cms_cert_fields_are_null(http, db):
    """Without CMS the cert fields must be null (not crash)."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
    )

    member = next(
        m for m in resp.json()["commission_members"]
        if m["admin_user_id"] == str(admin.id)
    )
    assert member["signer_cert_serial"] is None
    assert member["signer_cert_owner"] is None


# ── 4. invalid CMS rejected ────────────────────────────────────────────────────

async def test_sign_with_garbage_cms_returns_422(http, db):
    """A CMS body that is not valid Base64/DER must be rejected with 422."""
    admin, token, protocol = await _protocol_awaiting(db)

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign",
        headers=auth(token),
        json={"cms": "not-valid-cms!!!"},
    )

    assert resp.status_code == 422, resp.text
