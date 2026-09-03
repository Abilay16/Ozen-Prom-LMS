"""certificates v3 - add protocol/participant/training_type and denormalized fields

Revision ID: 0008_certificates_v3
Revises: 0007_user_photo
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0008_certificates_v3'
down_revision = '0007_user_photo'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Drop old FKs
    op.drop_constraint('certificates_user_id_fkey', 'certificates', type_='foreignkey')
    op.drop_constraint('certificates_assignment_id_fkey', 'certificates', type_='foreignkey')

    # 2. Drop columns that no longer exist in the model
    op.drop_column('certificates', 'assignment_id')
    op.drop_column('certificates', 'file_path')
    op.drop_column('certificates', 'issued_at')

    # 3. Add new columns (table is empty so nullable constraints are safe)
    op.add_column('certificates', sa.Column('protocol_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('certificates', sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('certificates', sa.Column('training_type_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('certificates', sa.Column('full_name', sa.String(255), nullable=True))
    op.add_column('certificates', sa.Column('organization_name', sa.String(255), nullable=True))
    op.add_column('certificates', sa.Column('position', sa.String(255), nullable=True))
    op.add_column('certificates', sa.Column('issued_date', sa.Date(), nullable=True))
    op.add_column('certificates', sa.Column('is_renewal', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('certificates', sa.Column('pdf_path', sa.String(512), nullable=True))
    op.add_column('certificates', sa.Column('qr_code_path', sa.String(512), nullable=True))
    op.add_column('certificates', sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))

    # 4. Alter existing columns
    op.alter_column('certificates', 'user_id', nullable=True)
    op.alter_column('certificates', 'valid_until',
                    type_=sa.Date(),
                    postgresql_using='valid_until::date',
                    existing_type=sa.DateTime(timezone=True),
                    existing_nullable=True)

    # 5. Add new FKs
    op.create_foreign_key('certificates_user_id_fkey', 'certificates', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('certificates_protocol_id_fkey', 'certificates', 'protocols', ['protocol_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('certificates_participant_id_fkey', 'certificates', 'protocol_participants', ['participant_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('certificates_training_type_id_fkey', 'certificates', 'training_types', ['training_type_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('certificates_training_type_id_fkey', 'certificates', type_='foreignkey')
    op.drop_constraint('certificates_participant_id_fkey', 'certificates', type_='foreignkey')
    op.drop_constraint('certificates_protocol_id_fkey', 'certificates', type_='foreignkey')
    op.drop_constraint('certificates_user_id_fkey', 'certificates', type_='foreignkey')

    op.drop_column('certificates', 'created_at')
    op.drop_column('certificates', 'qr_code_path')
    op.drop_column('certificates', 'pdf_path')
    op.drop_column('certificates', 'is_renewal')
    op.drop_column('certificates', 'issued_date')
    op.drop_column('certificates', 'position')
    op.drop_column('certificates', 'organization_name')
    op.drop_column('certificates', 'full_name')
    op.drop_column('certificates', 'training_type_id')
    op.drop_column('certificates', 'participant_id')
    op.drop_column('certificates', 'protocol_id')

    op.add_column('certificates', sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('certificates', sa.Column('file_path', sa.String(512), nullable=True))
    op.add_column('certificates', sa.Column('assignment_id', postgresql.UUID(as_uuid=True), nullable=True))
