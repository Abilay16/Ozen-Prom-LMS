"""add admin_users.organization_id + is_org_viewer

New read-only admin role: scoped to one organization, sees only that
organization's employees/streams/protocols/certificates/progress. NULL
organization_id (the default for every existing admin) means "not an
org viewer" — no behavior change for current accounts.

Revision ID: 0007_admin_org_viewer
Revises: 0006_tt_default_check_type
Create Date: 2026-11-13
"""
from alembic import op
import sqlalchemy as sa

revision = '0007_admin_org_viewer'
down_revision = '0006_tt_default_check_type'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('admin_users', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('admin_users', sa.Column('is_org_viewer', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key(
        'fk_admin_users_organization_id', 'admin_users', 'organizations',
        ['organization_id'], ['id'], ondelete='SET NULL',
    )


def downgrade():
    op.drop_constraint('fk_admin_users_organization_id', 'admin_users', type_='foreignkey')
    op.drop_column('admin_users', 'is_org_viewer')
    op.drop_column('admin_users', 'organization_id')
