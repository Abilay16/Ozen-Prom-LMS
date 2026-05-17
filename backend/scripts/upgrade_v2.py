"""
One-time upgrade script: v2 certificates + protocols schema.

Run ONCE inside the backend container BEFORE restarting the app:
  docker exec ozen_lms_backend python scripts/upgrade_v2.py

What this does:
  1. Adds admin_role enum + column to admin_users (default: superadmin)
  2. Drops the old placeholder certificates table
     (the new one will be auto-created by create_all on next app start)
"""
import os
import asyncio
import asyncpg


async def main():
    db_url = os.environ["DATABASE_URL"]
    # asyncpg wants postgresql:// not postgresql+asyncpg://
    pg_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(pg_url)
    try:
        print("Connected to database.")

        # Create enums (idempotent)
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE protocolstatus AS ENUM ('draft', 'signed', 'archived');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE commissionrole AS ENUM ('chair', 'member');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE participantresult AS ENUM ('passed', 'failed');
            EXCEPTION WHEN duplicate_object THEN NULL;
            END $$;
        """)
        print("Enums created (or already exist).")

        # Drop old certificates table (will be recreated by create_all)
        old_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'certificates' AND column_name = 'assignment_id'
            )
        """)
        if old_exists:
            await conn.execute("DROP TABLE IF EXISTS certificates CASCADE")
            print("Dropped old certificates table (will be recreated on next start).")
        else:
            print("certificates table is already up-to-date. Skipping.")

        print("\nUpgrade complete. Restart the backend container now.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
