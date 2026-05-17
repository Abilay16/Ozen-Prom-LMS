"""add commission eligibility fields and check_type

Revision ID: 0004_commission_eligible_check_type
Revises: 0003_eds_signature_fields
Create Date: 2026-05-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_commission_check'
down_revision = '0003_eds_signature_fields'
branch_labels = None
depends_on = None

checktype_enum = sa.Enum(
    'первичный', 'периодический', 'повторный', 'внеплановый',
    name='checktype'
)


def upgrade() -> None:
    # Create the enum type explicitly so it exists before the column
    checktype_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('protocols',
        sa.Column('check_type', checktype_enum, nullable=True))

    op.add_column('admin_users',
        sa.Column('is_commission_eligible', sa.Boolean(),
                  server_default='false', nullable=False))
    op.add_column('admin_users',
        sa.Column('position_title', sa.String(512), nullable=True))

    op.add_column('protocol_participants',
        sa.Column('organization_name', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('protocol_participants', 'organization_name')
    op.drop_column('admin_users', 'position_title')
    op.drop_column('admin_users', 'is_commission_eligible')
    op.drop_column('protocols', 'check_type')
    checktype_enum.drop(op.get_bind(), checkfirst=True)
