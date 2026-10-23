"""add protocol_commission_members.signer_crypto_verified

Marks whether a commission member's ЭЦП signature was actually
cryptographically verified (signature bytes checked against the real
НУЦ РК root chain) as opposed to only having its certificate's name and
expiry date checked, which is all the system did before this migration.
NULL for every row signed before this column existed — those signatures
were never crypto-verified, this doesn't retroactively change what
happened, it just couldn't be recorded at the time.

Revision ID: 0005_eds_crypto_verified
Revises: 0004_protocol_validity_override
Create Date: 2026-10-23
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_eds_crypto_verified'
down_revision = '0004_protocol_validity_override'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('protocol_commission_members', sa.Column('signer_crypto_verified', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('protocol_commission_members', 'signer_crypto_verified')
