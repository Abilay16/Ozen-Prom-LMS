"""
Seed script — creates / updates real commission member accounts for Ozen-Prom.

  Председатель:
    login: ayapbergenov      full_name: Аяпбергенов Алпамыс Аскарұлы
    position: Заместитель директора ТОО «Озен-Пром»

  Члены:
    login: dzhajgulova       full_name: Джайгулова Ұлболсын Серікқызы
    login: aliev             full_name: Алиев Абылай Илиясулы
    position: Инженер по охране труда и технике безопасности ТОО «Озен-Пром»

Usage:
  docker compose exec backend python -m scripts.seed_commission
or:
  cd backend && python -m scripts.seed_commission

Idempotent: safe to run multiple times.
If account already exists — full_name and position_title are updated,
password is NOT changed (printed would be the initial password if newly created).
"""
import asyncio
import sys
import os
import secrets
import string

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import AdminUser

POSITION_OT = "Инженер по охране труда и технике безопасности ТОО «Озен-Пром»"
POSITION_CHAIR = "Заместитель директора ТОО «Озен-Пром»"

COMMISSION_MEMBERS = [
    {
        "login": "ayapbergenov",
        "full_name": "Аяпбергенов Алпамыс Аскарұлы",
        "position_title": POSITION_CHAIR,
        "is_commission_eligible": True,
        "is_superadmin": False,
    },
    {
        "login": "dzhajgulova",
        "full_name": "Джайгулова Ұлболсын Серікқызы",
        "position_title": POSITION_OT,
        "is_commission_eligible": True,
        "is_superadmin": False,
    },
    {
        "login": "aliev",
        "full_name": "Алиев Абылай Илиясулы",
        "position_title": POSITION_OT,
        "is_commission_eligible": True,
        "is_superadmin": False,
    },
]


def _gen_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "@#!"
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        # ensure at least one of each required char class
        if (any(c.isupper() for c in pwd)
                and any(c.islower() for c in pwd)
                and any(c.isdigit() for c in pwd)):
            return pwd


async def main():
    print("=== Создание / обновление членов комиссии Озен-Пром ===\n")
    async with AsyncSessionLocal() as db:
        for spec in COMMISSION_MEMBERS:
            existing = (
                await db.execute(
                    select(AdminUser).where(AdminUser.login == spec["login"])
                )
            ).scalar_one_or_none()

            if existing:
                # Update metadata but keep password unchanged
                existing.full_name = spec["full_name"]
                existing.position_title = spec["position_title"]
                existing.is_commission_eligible = spec["is_commission_eligible"]
                existing.is_superadmin = spec["is_superadmin"]
                print(f"  [обновлён] login='{spec['login']}'  ФИО='{spec['full_name']}'")
            else:
                pwd = _gen_password()
                user = AdminUser(
                    login=spec["login"],
                    password_hash=hash_password(pwd),
                    full_name=spec["full_name"],
                    position_title=spec["position_title"],
                    is_commission_eligible=spec["is_commission_eligible"],
                    is_superadmin=spec["is_superadmin"],
                    is_active=True,
                )
                db.add(user)
                print(
                    f"  [+создан] login='{spec['login']}'  "
                    f"пароль='{pwd}'  ФИО='{spec['full_name']}'"
                )

        await db.commit()

    print("\n✓ Готово. Пароли новых аккаунтов указаны выше — сохраните их!")
    print("  Пароли существующих аккаунтов не изменялись.")


if __name__ == "__main__":
    asyncio.run(main())
