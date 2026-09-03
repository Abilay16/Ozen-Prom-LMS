"""base schema — squashed snapshot of the full current schema

This migration replaces the previous chain (0002..0008), which never had a
real "revision 1" — the base tables were always created via
`Base.metadata.create_all()` at app startup, not through Alembic. That left
Alembic's history out of sync with what actually exists in the database,
which is risky for schema evolution going forward.

This single migration creates the ENTIRE current schema (all tables, enums,
indexes, constraints) from scratch, generated from `pg_dump --schema-only`
against a real database that was verified (via `alembic check`) to match
the current SQLAlchemy models. The old 0002..0008 migration files are kept
for historical reference in `alembic/versions/_archived_pre_squash/` but are
no longer part of the active chain.

IMPORTANT — one-time step for any EXISTING database (dev or prod) that
already has this schema (created via the old create_all() + partial
migrations): do NOT run `alembic upgrade head` for this migration, it would
try to CREATE tables that already exist and fail. Instead, stamp the
database as already being at this revision:

    alembic stamp 0001_base_schema

Only a genuinely empty/fresh database should run `alembic upgrade head`
against this migration.

Revision ID: 0001_base_schema
Revises:
Create Date: 2026-09-02
"""
import os

from alembic import op

revision = '0001_base_schema'
down_revision = None
branch_labels = None
depends_on = None

_SQL_FILE = os.path.join(os.path.dirname(__file__), '0001_base_schema.sql')


def upgrade() -> None:
    with open(_SQL_FILE, encoding='utf-8') as f:
        sql = f.read()
    bind = op.get_bind()
    # asyncpg's prepared-statement path refuses to run more than one SQL
    # command per execute() call, so split the dump into individual
    # statements (safe here — the dump has no dollar-quoted function
    # bodies or embedded semicolons, verified against this file).
    for statement in sql.split(';\n'):
        statement = statement.strip()
        if not statement:
            continue
        # pg_dump clears search_path for safety ("SELECT
        # pg_catalog.set_config('search_path', '', false)") — skip it, it
        # would break Alembic's own unqualified alembic_version lookups
        # for the rest of this session. All our statements are already
        # schema-qualified (public.xxx), so clearing search_path adds
        # nothing here.
        if "set_config('search_path'" in statement:
            continue
        # A chunk that is comment lines only (e.g. the trailing
        # "-- PostgreSQL database dump complete --" footer) has no real
        # SQL in it — sending it to asyncpg trips an unrelated internal
        # error in the driver, so skip it explicitly instead of relying
        # on it being a harmless no-op.
        if all(line.strip().startswith('--') or not line.strip() for line in statement.splitlines()):
            continue
        # Each chunk between semicolons commonly starts with a pg_dump
        # "-- Name: ...; Type: ...\n--\n" comment header followed by the
        # real DDL — do NOT skip these just because they start with '--'.
        # Only a chunk that is comment lines only (no real SQL at all)
        # is a genuine no-op; execute()-ing it is harmless anyway.
        #
        # exec_driver_sql (not op.execute) sends the string straight to
        # the DBAPI without going through SQLAlchemy's text()/bind-param
        # parsing — needed because this SQL contains literal ':' via
        # Postgres '::type' casts, which text() would otherwise try to
        # interpret as bind parameters.
        bind.exec_driver_sql(statement)


def downgrade() -> None:
    op.execute('DROP SCHEMA public CASCADE')
    op.execute('CREATE SCHEMA public')
