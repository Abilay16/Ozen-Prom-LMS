"""
One-off backfill: fill in missing organization_name on already-existing
protocol participants and certificates.

Root cause (fixed going forward in app/api/v1/protocols.py): when a
protocol/batch itself had no organization set, participants and their
certificates got organization_name=None even though the worker's own user
profile had an organization — showing up as "Место работы: —" on their
certificate. This script repairs rows created before that fix.

Safe to re-run: only touches rows where organization_name is currently
NULL or empty, and only sets it when a value can actually be found.

Usage (inside the backend container):
    docker compose exec backend python scripts/backfill_organization_names.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, or_

from app.core.database import AsyncSessionLocal
from app.models.protocol import ProtocolParticipant, Protocol
from app.models.certificate import Certificate
from app.models.user import User
from app.models.batch import TrainingBatch
from app.models.organization import Organization


async def main():
    async with AsyncSessionLocal() as db:
        # 1. Backfill ProtocolParticipant.organization_name from the linked
        #    user's own organization, or the protocol's/batch's organization.
        result = await db.execute(
            select(ProtocolParticipant).where(
                or_(ProtocolParticipant.organization_name.is_(None), ProtocolParticipant.organization_name == "")
            )
        )
        participants = result.scalars().all()
        fixed_participants = 0
        for p in participants:
            org_name = None
            if p.user_id:
                user = (await db.execute(select(User).where(User.id == p.user_id))).scalar_one_or_none()
                if user and user.organization_id:
                    org = (await db.execute(select(Organization).where(Organization.id == user.organization_id))).scalar_one_or_none()
                    org_name = org.name if org else None
            if not org_name:
                proto = (await db.execute(select(Protocol).where(Protocol.id == p.protocol_id))).scalar_one_or_none()
                if proto:
                    org_id = proto.organization_id
                    if not org_id and proto.batch_id:
                        batch = (await db.execute(select(TrainingBatch).where(TrainingBatch.id == proto.batch_id))).scalar_one_or_none()
                        org_id = batch.organization_id if batch else None
                    if org_id:
                        org = (await db.execute(select(Organization).where(Organization.id == org_id))).scalar_one_or_none()
                        org_name = org.name if org else None
            if org_name:
                p.organization_name = org_name
                fixed_participants += 1

        # 2. Backfill Certificate.organization_name from its participant
        #    (now fixed above) or the same user/protocol fallback chain.
        result = await db.execute(
            select(Certificate).where(
                or_(Certificate.organization_name.is_(None), Certificate.organization_name == "")
            )
        )
        certs = result.scalars().all()
        fixed_certs = 0
        for c in certs:
            org_name = None
            if c.participant_id:
                part = (await db.execute(select(ProtocolParticipant).where(ProtocolParticipant.id == c.participant_id))).scalar_one_or_none()
                if part:
                    org_name = part.organization_name
            if not org_name and c.user_id:
                user = (await db.execute(select(User).where(User.id == c.user_id))).scalar_one_or_none()
                if user and user.organization_id:
                    org = (await db.execute(select(Organization).where(Organization.id == user.organization_id))).scalar_one_or_none()
                    org_name = org.name if org else None
            if org_name:
                c.organization_name = org_name
                fixed_certs += 1

        await db.commit()
        print(f"Fixed {fixed_participants} protocol participant(s), {fixed_certs} certificate(s).")


if __name__ == "__main__":
    asyncio.run(main())
