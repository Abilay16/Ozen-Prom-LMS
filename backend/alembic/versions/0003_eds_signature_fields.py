"""add EDS signature fields to protocol_commission_members

Revision ID: 0003_eds_signature_fields
Revises: 0002_certificates_v2
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_eds_signature_fields'
down_revision = '0002_certificates_v2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('protocol_commission_members',
        sa.Column('signature_cms', sa.Text, nullable=True))
    op.add_column('protocol_commission_members',
        sa.Column('signer_cert_serial', sa.String(100), nullable=True))
    op.add_column('protocol_commission_members',
        sa.Column('signer_cert_owner', sa.String(512), nullable=True))
    op.add_column('protocol_commission_members',
        sa.Column('signer_cert_valid_from', sa.DateTime(timezone=True), nullable=True))
    op.add_column('protocol_commission_members',
        sa.Column('signer_cert_valid_to', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('protocol_commission_members', 'signer_cert_valid_to')
    op.drop_column('protocol_commission_members', 'signer_cert_valid_from')
    op.drop_column('protocol_commission_members', 'signer_cert_owner')
    op.drop_column('protocol_commission_members', 'signer_cert_serial')
    op.drop_column('protocol_commission_members', 'signature_cms')
