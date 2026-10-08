"""
One-off fix: set the organization on protocols whose organization ended up
empty (shown as "—" in the admin protocols list), and propagate it to every
participant and already-issued certificate under those protocols.

Why this happens: a protocol's organization is only resolved from the
protocol's own organization_id or its batch's organization_id at the time
participants are imported / certificates are issued (see
app/api/v1/protocols.py). If neither had an organization set — e.g. the
protocol was created standalone, or participants were added manually
without an organization — every participant and certificate under it keeps
organization_name=None forever, even if fixed later, because those are
point-in-time snapshots.

This script finds protocols by protocol_number, sets their organization_id
to the given organization (created if it doesn't exist), and backfills
organization_name on every participant and certificate under those
protocols — but ONLY rows that are currently empty, unless --force is
passed. Matches multiple protocols that share the same protocol_number
(different training types can share a number) — review the --dry-run
output before running for real.

Usage (inside the backend container):
    docker compose exec backend python scripts/set_protocol_organization.py \
        --protocol-number 217 \
        --organization 'ТОО "Equipment support"' \
        --dry-run

Then drop --dry-run to actually write.
"""
import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.protocol import Protocol, ProtocolParticipant
from app.models.certificate import Certificate
from app.models.training_type import TrainingType


async def main(protocol_number: str, org_name: str, dry_run: bool, force: bool):
    async with AsyncSessionLocal() as db:
        org = (await db.execute(select(Organization).where(Organization.name == org_name))).scalar_one_or_none()
        if not org:
            print(f'Organization {org_name!r} not found — it will be created.')
            if not dry_run:
                org = Organization(name=org_name, is_active=True)
                db.add(org)
                await db.flush()

        protocols = (await db.execute(
            select(Protocol)
            .options(selectinload(Protocol.participants), selectinload(Protocol.training_type))
            .where(Protocol.protocol_number == protocol_number)
        )).scalars().all()

        if not protocols:
            print(f'No protocols found with protocol_number={protocol_number!r}')
            return

        print(f'Found {len(protocols)} protocol(s) with number {protocol_number!r}:')
        total_participants = 0
        total_certs = 0
        for p in protocols:
            tt_name = p.training_type.name_short if p.training_type else "?"
            current_org = p.organization_id
            print(f'  - {p.id}  [{tt_name}]  exam_date={p.exam_date}  organization_id={current_org}  participants={len(p.participants)}')
            if current_org and not force:
                print(f'    -> SKIPPING (already has an organization; pass --force to override)')
                continue
            total_participants += len(p.participants)

            certs = (await db.execute(
                select(Certificate).where(Certificate.protocol_id == p.id)
            )).scalars().all()
            total_certs += len(certs)

            if dry_run:
                continue

            p.organization_id = org.id
            for part in p.participants:
                if force or not part.organization_name:
                    part.organization_name = org_name
            for c in certs:
                if force or not c.organization_name:
                    c.organization_name = org_name

        print(f'Participants to update: {total_participants}')
        print(f'Certificates to update: {total_certs}')

        if dry_run:
            print('Dry run — no changes written.')
            return

        await db.commit()
        print('Done.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-number", required=True, help="Protocol number to match (e.g. 217)")
    parser.add_argument("--organization", required=True, help="Full organization name to set, e.g. 'ТОО \"Equipment support\"'")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    parser.add_argument("--force", action="store_true", help="Overwrite even protocols/rows that already have an organization set")
    args = parser.parse_args()
    asyncio.run(main(args.protocol_number, args.organization, args.dry_run, args.force))
