"""add users.education

Lets an admin record a worker's education level (высшее / среднее /
среднее специальное) on their profile, so it can flow through to the
"Образование" column on ПромБез-style protocols instead of always being
blank — see app/api/v1/protocols.py import_from_batch, which now copies
it onto each ProtocolParticipant at import time.

Revision ID: 0003_user_education
Revises: 0002_protocol_defaults
Create Date: 2026-10-15
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_user_education'
down_revision = '0002_protocol_defaults'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('education', sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column('users', 'education')
