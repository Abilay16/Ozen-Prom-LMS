"""add user_documents and medical_exams tables

Revision ID: 0006_med_docs
Revises: 0005_verify_token
Create Date: 2026-05-14
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0006_med_docs'
down_revision = '0005_verify_token'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── user_documents ────────────────────────────────────────────────────────
    op.create_table(
        'user_documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index('ix_user_documents_user_id', 'user_documents', ['user_id'])

    # ── medical_exams ─────────────────────────────────────────────────────────
    op.create_table(
        'medical_exams',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', UUID(as_uuid=True),
                  sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(10), nullable=True),
        sa.Column('workplace', sa.String(255), nullable=True),
        sa.Column('position', sa.String(255), nullable=True),
        sa.Column('icd10_group', sa.Text(), nullable=True),
        sa.Column('fit_for_work', sa.Boolean(), nullable=True),
        sa.Column('exam_date', sa.Date(), nullable=True),
        sa.Column('source_file', sa.String(255), nullable=True),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index('ix_medical_exams_user_id', 'medical_exams', ['user_id'])
    op.create_index('ix_medical_exams_organization_id', 'medical_exams', ['organization_id'])


def downgrade() -> None:
    op.drop_table('medical_exams')
    op.drop_table('user_documents')
