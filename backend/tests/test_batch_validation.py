"""
P1 Feature — Batch all-passed validation.

Rule: importing participants from a batch is only allowed when ALL users in
that batch have assignment status = passed.  Any other status (assigned,
in_progress, failed) must produce a 409 error.
"""
import pytest
from app.models.assignment import AssignmentStatus
from tests.conftest import (
    make_admin, make_training_type, make_batch_with_users, make_protocol,
)


# ── helpers ───────────────────────────────────────────────────────────────────

def auth(token):
    return {"Authorization": f"Bearer {token}"}


async def import_url(protocol_id):
    return f"/api/v1/admin/protocols/{protocol_id}/import-participants"


# ── tests ─────────────────────────────────────────────────────────────────────

async def test_import_blocked_when_user_has_assigned_status(http, db):
    """assigned = hasn't started yet → must be blocked."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, _users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.assigned, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 409, resp.text
    assert "завершили обучение" in resp.json()["detail"]


async def test_import_blocked_when_user_has_in_progress_status(http, db):
    """in_progress = currently taking the course → must be blocked."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, _users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.in_progress, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 409, resp.text


async def test_import_blocked_when_user_has_failed_status(http, db):
    """failed = didn't pass → must be blocked (all must have passed)."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, _users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.failed, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 409, resp.text


async def test_import_allowed_when_all_users_passed(http, db):
    """All passed → import should succeed and add participants."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.passed, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["added"] == 2
    assert len(data["protocol"]["participants"]) == 2


async def test_import_error_message_mentions_non_passed_user(http, db):
    """Error detail should mention the name of the user who hasn't finished."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.in_progress]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 409
    # The error message should name the problematic user
    detail = resp.json()["detail"]
    assert users[0].full_name in detail


async def test_import_empty_batch_still_allowed(http, db):
    """A batch with no assignments at all → nothing to import, added=0, no 409."""
    from app.models.batch import TrainingBatch, BatchStatus
    from uuid import uuid4

    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    empty_batch = TrainingBatch(id=uuid4(), name="Empty batch", status=BatchStatus.completed)
    db.add(empty_batch)
    await db.flush()
    protocol = await make_protocol(db, admin, tt, empty_batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["added"] == 0
