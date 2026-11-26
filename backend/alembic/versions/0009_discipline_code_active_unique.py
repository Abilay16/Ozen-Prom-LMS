"""discipline code unique only among active disciplines

Дисциплины не удаляются, а уходят в архив (is_active = false): на них
ссылаются назначения сотрудников. Раньше код был уникален среди всех,
и новую дисциплину нельзя было завести с кодом архивной — вместо неё
оживала старая. Теперь код уникален только среди действующих.

Revision ID: 0009_discipline_code_active
Revises: 0008_seed_training_types
Create Date: 2026-11-26
"""
from alembic import op

revision = '0009_discipline_code_active'
down_revision = '0008_seed_training_types'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE disciplines DROP CONSTRAINT IF EXISTS disciplines_code_key")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_disciplines_code_active "
        "ON disciplines (code) WHERE is_active"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_disciplines_code_active")
    # Обратно вернётся, только если среди архивных нет повторов кода.
    op.execute("ALTER TABLE disciplines ADD CONSTRAINT disciplines_code_key UNIQUE (code)")
