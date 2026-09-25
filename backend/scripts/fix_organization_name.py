"""
One-off fix: correct an organization's name (e.g. wrong legal form prefix
like "ТОО" instead of "ЧУ") and propagate the correction to every already
-issued protocol participant row and certificate that snapshotted the old
name at creation time.

Why a script and not just renaming in the admin UI: Organization.name is
only the live master record. ProtocolParticipant.organization_name and
Certificate.organization_name are copied from it at the moment a person is
added to a protocol / a certificate is issued (so a protocol from last year
keeps showing the org as it was named back then, which is normally the
correct behavior for a legal record) — renaming the organization alone
would fix all FUTURE protocols/certificates but leave already-issued ones
showing the old (wrong) name forever. This script fixes both: the master
record, and every already-issued snapshot that has the exact old text.

Safe to re-run: only touches rows whose organization_name matches the old
name exactly; matching rows already fixed are simply not found on a second
run.

Usage (inside the backend container):
    docker compose exec backend python scripts/fix_organization_name.py \
        --old 'ТОО "Samruk Business Academy"' \
        --new 'ЧУ "Samruk Business Academy"'

Add --dry-run to see what would change without writing anything.
"""
import argparse
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.organization import Organization
from app.models.protocol import ProtocolParticipant
from app.models.certificate import Certificate


async def main(old_name: str, new_name: str, dry_run: bool):
    async with AsyncSessionLocal() as db:
        org = (await db.execute(select(Organization).where(Organization.name == old_name))).scalar_one_or_none()
        if not org:
            print(f'No organization found with name exactly: {old_name!r}')
            print('Check the exact spelling/quotes — organizations list:')
            all_orgs = (await db.execute(select(Organization.name))).scalars().all()
            for n in all_orgs:
                print(' -', n)
            return

        participants = (await db.execute(
            select(ProtocolParticipant).where(ProtocolParticipant.organization_name == old_name)
        )).scalars().all()
        certs = (await db.execute(
            select(Certificate).where(Certificate.organization_name == old_name)
        )).scalars().all()

        print(f'Organization: {org.name!r} -> {new_name!r}')
        print(f'Protocol participants to fix: {len(participants)}')
        print(f'Certificates to fix: {len(certs)}')

        if dry_run:
            print('Dry run — no changes written.')
            return

        org.name = new_name
        for p in participants:
            p.organization_name = new_name
        for c in certs:
            c.organization_name = new_name

        await db.commit()
        print('Done.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, help="Exact current organization name")
    parser.add_argument("--new", required=True, help="Corrected organization name")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()
    asyncio.run(main(args.old, args.new, args.dry_run))
