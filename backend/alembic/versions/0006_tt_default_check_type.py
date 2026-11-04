"""add training_types.default_check_type + set current protocol defaults

Lets the БиОТ/ПромБез/ПТМ check-type (периодический/первичный/...) prefill
the same way order_number/order_date/legal_basis already do when a new
protocol is created — still editable afterwards, never touches existing
protocols. Also updates the three training types' current default
order_number/order_date/check_type to the values requested 2026-11-04.

Revision ID: 0006_training_type_default_check_type
Revises: 0005_eds_crypto_verified
Create Date: 2026-11-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_tt_default_check_type'
down_revision = '0005_eds_crypto_verified'
branch_labels = None
depends_on = None

CHECKTYPE = sa.Enum('primary', 'periodic', 'repeat', 'unplanned', name='checktype', create_type=False)


def upgrade():
    op.add_column('training_types', sa.Column('default_check_type', CHECKTYPE, nullable=True))

    conn = op.get_bind()
    conn.execute(sa.text(
        "UPDATE training_types SET default_order_number = '8', default_order_date = '2025-02-24', "
        "default_check_type = 'periodic' WHERE code = 'biot'"
    ))
    conn.execute(sa.text(
        "UPDATE training_types SET default_order_number = '8', default_order_date = '2025-02-24' "
        "WHERE code = 'prombez'"
    ))
    conn.execute(sa.text(
        "UPDATE training_types SET default_order_number = '09 пп', default_order_date = '2025-02-27' "
        "WHERE code = 'ptm'"
    ))


def downgrade():
    op.drop_column('training_types', 'default_check_type')
