"""
P1 Feature — Auto-issue certificates when protocol is signed.

Rule: when the last required commission member signs (making status → signed),
certificates must be auto-created for all participants whose result = passed.
Participants with result = failed or result = None get no certificate.
A second signing attempt (idempotent re-run) must NOT create duplicate certs.
"""
import pytest
from datetime import datetime, timezone
from app.models.assignment import AssignmentStatus
from app.models.protocol import ParticipantResult, CommissionRole, ProtocolStatus
from tests.conftest import (
    make_admin, make_training_type, make_batch_with_users, make_protocol,
    make_commission_member,
)
from app.models.protocol import ProtocolParticipant, ProtocolCommissionMember
from uuid import uuid4


# ── helper ────────────────────────────────────────────────────────────────────

def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _protocol_awaiting_with_participants(db, results: list[ParticipantResult | None]):
    """
    Build a ready-to-sign protocol:
     - one commission member (= admin, role=member, no chair)
     - participants with given results
     - status = awaiting_signatures
    """
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    protocol = await make_protocol(db, admin, tt, batch=None)
    await make_commission_member(db, protocol, admin, role=CommissionRole.member)

    for i, result in enumerate(results):
        p = ProtocolParticipant(
            id=uuid4(), protocol_id=protocol.id,
            full_name=f"Участник {i+1}",
            position="Инженер",
            result=result,
            sort_order=i,
        )
        db.add(p)

    protocol.status = ProtocolStatus.awaiting_signatures
    await db.flush()
    await db.commit()
    return admin, token, protocol


# ── tests ─────────────────────────────────────────────────────────────────────

async def test_sign_auto_issues_cert_for_passed_participant(http, db):
    """Signing the last slot → certificate is auto-created for passed participant."""
    admin, token, protocol = await _protocol_awaiting_with_participants(
        db, [ParticipantResult.passed]
    )

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign", headers=auth(token)
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "signed"
    passed = next(p for p in data["participants"] if p["result"] == "passed")
    assert passed["certificate_id"] is not None


async def test_sign_does_not_issue_cert_for_failed_participant(http, db):
    """Failed participants must not receive a certificate."""
    admin, token, protocol = await _protocol_awaiting_with_participants(
        db, [ParticipantResult.passed, ParticipantResult.failed]
    )

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign", headers=auth(token)
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    failed = next(p for p in data["participants"] if p["result"] == "failed")
    assert failed["certificate_id"] is None


async def test_sign_does_not_issue_cert_for_result_none(http, db):
    """Participant with no result set must not receive a certificate."""
    admin, token, protocol = await _protocol_awaiting_with_participants(
        db, [ParticipantResult.passed, None]
    )

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign", headers=auth(token)
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    no_result = next(p for p in data["participants"] if p["result"] is None)
    assert no_result["certificate_id"] is None


async def test_sign_issues_certs_for_all_passed_participants(http, db):
    """All three passed participants each get their own certificate."""
    admin, token, protocol = await _protocol_awaiting_with_participants(
        db, [ParticipantResult.passed, ParticipantResult.passed, ParticipantResult.passed]
    )

    resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign", headers=auth(token)
    )

    assert resp.status_code == 200, resp.text
    participants = resp.json()["participants"]
    cert_ids = [p["certificate_id"] for p in participants]
    assert all(c is not None for c in cert_ids), "Every passed participant needs a cert"
    assert len(set(cert_ids)) == 3, "Each participant must get a distinct certificate"


async def test_manual_issue_certs_is_idempotent_after_auto_issue(http, db):
    """
    If certs were already auto-issued on signing, calling /issue-certificates
    manually must not create duplicates (added=0, no 500).
    """
    admin, token, protocol = await _protocol_awaiting_with_participants(
        db, [ParticipantResult.passed]
    )

    # Sign → auto-issue
    sign_resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/sign", headers=auth(token)
    )
    assert sign_resp.status_code == 200
    assert sign_resp.json()["status"] == "signed"

    # Manual issue on already-signed protocol (button is technically hidden in UI,
    # but the endpoint must be safe to call)
    issue_resp = await http.post(
        f"/api/v1/admin/protocols/{protocol.id}/issue-certificates", headers=auth(token)
    )
    assert issue_resp.status_code == 200, issue_resp.text
    # No new certificates should be issued (all already have one)
    assert issue_resp.json()["issued"] == []
