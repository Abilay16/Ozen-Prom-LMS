"""seed base training types (БиОТ, ПТМ, ПромБез, ЭлБез)

Справочник типов обучения раньше заводился вручную и в миграциях не было
ни одной строки — на чистой базе (новая установка, CI, корпоративная версия)
нельзя создать ни один протокол. Вставляем 4 базовых типа, только если
такого кода ещё нет: на существующих базах миграция ничего не меняет.

Revision ID: 0008_seed_training_types
Revises: 0007_admin_org_viewer
Create Date: 2026-11-23
"""
from alembic import op

revision = '0008_seed_training_types'
down_revision = '0007_admin_org_viewer'
branch_labels = None
depends_on = None


TYPES = [
    # code, name_ru, name_short, validity_years
    ('biot', 'Безопасность и охрана труда', 'БиОТ', 1),
    ('ptm', 'Пожарно-технический минимум', 'ПТМ', 3),
    ('prombez', 'Промышленная безопасность', 'ПромБез', 1),
    ('elektro', 'Электробезопасность', 'ЭлБез', 1),
]


def upgrade():
    for code, name_ru, name_short, years in TYPES:
        op.execute(
            "INSERT INTO training_types (id, code, name_ru, name_short, validity_years, is_active) "
            f"VALUES (gen_random_uuid(), '{code}', '{name_ru}', '{name_short}', {years}, true) "
            "ON CONFLICT (code) DO NOTHING"
        )


def downgrade():
    # Не удаляем: на типы ссылаются протоколы и удостоверения.
    pass
