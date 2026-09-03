"""
P1 Feature — Batch partial-import behavior.

Rule: importing participants from a batch pulls in only users whose
assignment status = passed. Users with any other status (assigned,
in_progress, failed) are silently skipped — NOT blocked — so an admin can
create a protocol for whoever has finished so far without waiting for the
entire batch to complete (batches routinely have staggered completion
dates). A later re-import for the same batch/training type additionally
excludes anyone already certified by an earlier protocol — see
import_participants_from_batch in app/api/v1/protocols.py.
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

async def test_import_skips_user_with_assigned_status(http, db):
    """assigned = hasn't started yet → skipped, not blocked."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.assigned, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["added"] == 1
    names = [p["full_name"] for p in data["protocol"]["participants"]]
    assert users[0].full_name not in names  # the "assigned" one stays out
    assert users[1].full_name in names      # the "passed" one gets in


async def test_import_skips_user_with_in_progress_status(http, db):
    """in_progress = currently taking the course → skipped, not blocked."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.in_progress, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["added"] == 1


async def test_import_skips_user_with_failed_status(http, db):
    """failed = didn't pass → skipped, not blocked (only passed gets imported)."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.failed, AssignmentStatus.passed]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["added"] == 1


async def test_import_allowed_when_all_users_passed(http, db):
    """All passed → import should succeed and add every participant."""
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


async def test_import_only_in_progress_user_adds_nobody(http, db):
    """A batch where the only member hasn't passed yet → added=0, no 409
    (they simply aren't ready for a protocol yet; nothing to report as an
    error — the admin re-imports later once the person passes)."""
    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.in_progress]
    )
    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    assert resp.json()["added"] == 0


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


async def test_reimport_excludes_already_certified_participant(http, db):
    """A user already certified for this training_type in an EARLIER protocol
    must not be pulled into a new protocol's import — this is what makes the
    "skip, don't block" behavior above safe to rely on across multiple
    protocols for the same batch over time."""
    from app.models.protocol import Protocol, ProtocolParticipant, ParticipantResult

    admin, token = await make_admin(db)
    tt = await make_training_type(db)
    batch, users, _asgn = await make_batch_with_users(
        db, [AssignmentStatus.passed, AssignmentStatus.passed]
    )

    # Earlier protocol already certified users[0]
    earlier = Protocol(
        protocol_number="EARLIER-1", training_type_id=tt.id,
        exam_date=__import__("datetime").date(2026, 1, 1),
    )
    db.add(earlier)
    await db.flush()
    db.add(ProtocolParticipant(
        protocol_id=earlier.id, user_id=users[0].id,
        full_name=users[0].full_name, result=ParticipantResult.passed,
        sort_order=0,
    ))
    await db.flush()

    protocol = await make_protocol(db, admin, tt, batch)
    await db.commit()

    resp = await http.post(await import_url(protocol.id), headers=auth(token))

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["added"] == 1
    assert data["skipped_already_certified"] == 1
    names = [p["full_name"] for p in data["protocol"]["participants"]]
    assert users[0].full_name not in names
    assert users[1].full_name in names
