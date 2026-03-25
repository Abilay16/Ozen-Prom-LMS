"""
Seed script: creates the first superadmin account.
Usage:
  docker compose exec backend python -m scripts.seed_admin
or:
  cd backend && python -m scripts.seed_admin

Environment variables are read from .env via app.core.config
"""
import asyncio
import getpass
import sys
import os

# allow running from backend/ or root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import AdminUser


async def main():
    print("=== Создание администратора Оzen-Prom LMS ===")
    login = input("Логин администратора: ").strip()
    if not login:
        print("Логин не может быть пустым.")
        return

    password = getpass.getpass("Пароль: ")
    if len(password) < 8:
        print("Пароль должен быть не менее 8 символов.")
        return

    full_name = input("ФИО (опционально): ").strip() or "Суперадмин"

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(AdminUser).where(AdminUser.login == login))
        if existing.scalar_one_or_none():
            print(f"Администратор с логином '{login}' уже существует.")
            return

        admin = AdminUser(
            login=login,
            password_hash=hash_password(password),
            full_name=full_name,
            is_superadmin=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"\n✓ Администратор создан: login='{login}', id={admin.id}")


if __name__ == "__main__":
    asyncio.run(main())
