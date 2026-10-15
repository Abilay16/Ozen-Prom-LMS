"""add protocols.validity_years_override

БиОТ and ПромБез have a different certificate validity depending on
whether the worker is "рабочий" (1 year) or "ИТР" (3 years); ПТМ depends on
whether training was "с отрывом от производства" (3 years) or "без отрыва"
(1 year). Previously validity was always training_type.validity_years, a
single fixed number per type — wrong for about half of real cases. This
column lets a protocol override it; NULL keeps the training type's default
(used by types with no such split, e.g. ЭлБез).

Revision ID: 0004_protocol_validity_override
Revises: 0003_user_education
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_protocol_validity_override'
down_revision = '0003_user_education'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('protocols', sa.Column('validity_years_override', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('protocols', 'validity_years_override')
