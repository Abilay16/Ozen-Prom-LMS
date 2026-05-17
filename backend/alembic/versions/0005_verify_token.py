"""add verify_token to users

Revision ID: 0005_verify_token
Revises: 0004_commission_check
Create Date: 2026-05-11
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_verify_token'
down_revision = '0004_commission_check'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users',
        sa.Column('verify_token', sa.UUID(), nullable=True))

    # Populate all existing rows with a unique UUID
    op.execute("UPDATE users SET verify_token = gen_random_uuid() WHERE verify_token IS NULL")

    op.create_index('ix_users_verify_token', 'users', ['verify_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_verify_token', table_name='users')
    op.drop_column('users', 'verify_token')
