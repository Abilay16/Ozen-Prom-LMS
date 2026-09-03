"""add protocol auto-fill defaults (training type order/basis, default chair)

Adds:
  - training_types.default_order_number / default_order_date / default_legal_basis
    — prefill values used when a new protocol picks this training type.
  - admin_users.is_default_chair — which commission-eligible admin is picked
    as chair when a new protocol auto-populates its commission.

Also seeds the defaults the client provided for БиОТ / ПТМ / ПромБез, and
flags Аяпбергенов Алпамыс Аскарұлы (login "ayapbergenov") as the default
chair, matching what's already in production. Both are safe no-ops if the
rows don't exist (e.g. a fresh dev DB without that seed data).

Revision ID: 0002_protocol_defaults
Revises: 0001_base_schema
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_protocol_defaults'
down_revision = '0001_base_schema'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('training_types', sa.Column('default_order_number', sa.String(length=100), nullable=True))
    op.add_column('training_types', sa.Column('default_order_date', sa.Date(), nullable=True))
    op.add_column('training_types', sa.Column('default_legal_basis', sa.Text(), nullable=True))
    op.add_column('admin_users', sa.Column('is_default_chair', sa.Boolean(), nullable=False, server_default=sa.false()))

    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE training_types SET default_order_number = '1019', default_order_date = '2015-12-25', "
        "default_legal_basis = 'Подпункт 30 статьи 16 и статья 182 Трудового кодекса РК' WHERE code = 'biot'"
    ))
    conn.execute(sa.text(
        "UPDATE training_types SET default_order_number = '№276', default_order_date = '2014-06-09', "
        "default_legal_basis = 'Приказа МЧС РК №276' WHERE code = 'ptm'"
    ))
    conn.execute(sa.text(
        "UPDATE training_types SET default_order_number = '№332', default_order_date = '2026-02-24', "
        "default_legal_basis = 'На основании статьи 79 РК «О Гражданской защите» созданная приказом №8 от "
        "24 февраля 2025г. провела проверку знаний.' WHERE code = 'prombez'"
    ))
    conn.execute(sa.text("UPDATE admin_users SET is_default_chair = true WHERE login = 'ayapbergenov'"))


def downgrade():
    op.drop_column('admin_users', 'is_default_chair')
    op.drop_column('training_types', 'default_legal_basis')
    op.drop_column('training_types', 'default_order_date')
    op.drop_column('training_types', 'default_order_number')
