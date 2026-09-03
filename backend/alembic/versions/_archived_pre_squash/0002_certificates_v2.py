"""certificates_v2_protocols_training_types

Revision ID: 0002_certificates_v2
Revises:
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0002_certificates_v2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Enums ───────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE protocolstatus AS ENUM ('draft', 'signed', 'archived')")
    op.execute("CREATE TYPE commissionrole AS ENUM ('chair', 'member')")
    op.execute("CREATE TYPE participantresult AS ENUM ('passed', 'failed')")

    # ── admin_role column on admin_users ────────────────────────────────────
    op.add_column(
        'admin_users',
        sa.Column('admin_role', sa.Enum('superadmin', 'inspector', 'commission_chair', 'commission_member', name='adminrole'), nullable=False, server_default='superadmin')
    )

    # ── training_types ──────────────────────────────────────────────────────
    op.create_table(
        'training_types',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('name_ru', sa.String(255), nullable=False),
        sa.Column('name_short', sa.String(50), nullable=False),
        sa.Column('validity_years', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )

    # Seed reference data
    op.execute("""
        INSERT INTO training_types (id, code, name_ru, name_short, validity_years, is_active) VALUES
        (gen_random_uuid(), 'biot',    'Безопасность и охрана труда',                           'БиОТ',    1, true),
        (gen_random_uuid(), 'ptm',     'Пожарно-технический минимум',                            'ПТМ',     3, true),
        (gen_random_uuid(), 'prombez', 'Промышленная безопасность',                              'ПромБез', 1, true),
        (gen_random_uuid(), 'elektro', 'Электробезопасность',                                    'ЭлБез',   1, true)
    """)

    # ── protocols ───────────────────────────────────────────────────────────
    op.create_table(
        'protocols',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('protocol_number', sa.String(50), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('training_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('training_types.id', ondelete='SET NULL'), nullable=True),
        sa.Column('exam_date', sa.Date(), nullable=False),
        sa.Column('order_number', sa.String(100), nullable=True),
        sa.Column('order_date', sa.Date(), nullable=True),
        sa.Column('legal_basis', sa.Text(), nullable=True),
        sa.Column('regulatory_docs', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('draft', 'signed', 'archived', name='protocolstatus'), nullable=False, server_default='draft'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # ── protocol_commission_members ─────────────────────────────────────────
    op.create_table(
        'protocol_commission_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('protocol_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('protocols.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('admin_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('position_title', sa.String(255), nullable=True),
        sa.Column('role', sa.Enum('chair', 'member', name='commissionrole'), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    # ── protocol_participants ───────────────────────────────────────────────
    op.create_table(
        'protocol_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('protocol_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('protocols.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('position', sa.String(255), nullable=True),
        sa.Column('education', sa.String(100), nullable=True),
        sa.Column('result', sa.Enum('passed', 'failed', name='participantresult'), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
    )

    # ── certificates (drop old placeholder, create new) ────────────────────
    op.drop_table('certificates')
    op.create_table(
        'certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('certificate_number', sa.String(100), nullable=False, unique=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('protocol_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('protocols.id', ondelete='SET NULL'), nullable=True),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('protocol_participants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('training_type_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('training_types.id', ondelete='SET NULL'), nullable=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('organization_name', sa.String(255), nullable=True),
        sa.Column('position', sa.String(255), nullable=True),
        sa.Column('issued_date', sa.Date(), nullable=False),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('is_renewal', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pdf_path', sa.String(512), nullable=True),
        sa.Column('qr_code_path', sa.String(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('certificates')
    op.drop_table('protocol_participants')
    op.drop_table('protocol_commission_members')
    op.drop_table('protocols')
    op.drop_table('training_types')
    op.drop_column('admin_users', 'admin_role')
    op.execute("DROP TYPE IF EXISTS protocolstatus")
    op.execute("DROP TYPE IF EXISTS commissionrole")
    op.execute("DROP TYPE IF EXISTS participantresult")

    # Recreate original certificates placeholder
    op.create_table(
        'certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_course_assignments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('certificate_number', sa.String(100), nullable=True, unique=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_path', sa.String(512), nullable=True),
    )
