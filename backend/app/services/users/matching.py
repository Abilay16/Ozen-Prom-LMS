"""
Общие правила для импорта из Excel и ручного добавления в поток:
поиск/создание организации и поиск уже существующего сотрудника.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.models.user import User


def clean_org_name(name: str | None) -> str:
    return " ".join((name or "").split())


async def get_or_create_org(db: AsyncSession, name: str | None) -> Organization | None:
    name = clean_org_name(name)
    if not name:
        return None
    # Поиск в SQL без учёта регистра (раньше на каждую строку файла
    # грузились и перебирались все организации базы).
    org = (await db.execute(
        select(Organization)
        .where(func.lower(func.trim(Organization.name)) == name.lower())
        .order_by(Organization.created_at)
        .limit(1)
    )).scalar_one_or_none()
    if org:
        return org
    org = Organization(name=name, is_active=True)
    db.add(org)
    await db.flush()
    return org


async def find_existing_user(db: AsyncSession, normalized_full_name: str, organization_id) -> User | None:
    """Тот же человек = то же ФИО в той же организации.

    Если организация неизвестна, совпадением считаем только сотрудника тоже
    без организации. Раньше без организации искали по ФИО во всей базе — и
    новый «Ахметов Нурлан» склеивался с однофамильцем из чужой компании:
    получал его курсы, а свой аккаунт не создавался.
    """
    q = select(User).where(User.normalized_full_name == normalized_full_name)
    if organization_id:
        q = q.where(User.organization_id == organization_id)
    else:
        q = q.where(User.organization_id.is_(None))
    return (await db.execute(q.order_by(User.created_at).limit(1))).scalar_one_or_none()
