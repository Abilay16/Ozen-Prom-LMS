"""
Патч демо-протокола для живой демонстрации ЭЦП с одним сертификатом.

Что делает:
  • Джайгулова  (член)     → помечается как уже подписавшая (без ЭЦП)
  • Аяпбергенов (член)     → помечается как уже подписавший (без ЭЦП)
  • Алиев       (ПРЕДСЕДАТЕЛЬ) → не подписан — он подписывает вживую через NCALayer

После запуска:
  1. Войти как aliev → протокол BIOT-2026-001 → кнопка «Подписать» → ЭЦП
  2. Протокол становится «Подписан», удостоверения создаются автоматически

Usage:
  docker compose exec backend python -m scripts.presign_demo
"""
import asyncio
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.protocol import Protocol, ProtocolCommissionMember, CommissionRole

PROTOCOL_NUMBER = "BIOT-2026-001"


async def main():
    print(f"=== Пресостановка подписей для протокола {PROTOCOL_NUMBER} ===\n")

    async with AsyncSessionLocal() as db:
        proto = (await db.execute(
            select(Protocol).where(Protocol.protocol_number == PROTOCOL_NUMBER)
        )).scalar_one_or_none()

        if not proto:
            print(f"  ОШИБКА: протокол '{PROTOCOL_NUMBER}' не найден.")
            print("  Запустите сначала: python -m scripts.seed_demo")
            return

        members = (await db.execute(
            select(ProtocolCommissionMember)
            .where(ProtocolCommissionMember.protocol_id == proto.id)
        )).scalars().all()

        if not members:
            print("  ОШИБКА: у протокола нет членов комиссии.")
            return

        now = datetime.now(timezone.utc)

        for m in members:
            login = None
            # Определяем логин через admin_user
            if m.admin_user_id:
                from app.models.user import AdminUser
                admin = (await db.execute(
                    select(AdminUser).where(AdminUser.id == m.admin_user_id)
                )).scalar_one_or_none()
                login = admin.login if admin else None

            if login == "aliev":
                # Алиев — председатель, не подписан
                m.role = CommissionRole.chair
                m.signed_at = None
                m.signature_cms = None
                print(f"  [председатель, не подписан] {m.full_name}  (aliev)")

            else:
                # Остальные — члены, уже подписаны (без ЭЦП)
                m.role = CommissionRole.member
                m.signed_at = now
                m.signature_cms = None  # без ЭЦП
                print(f"  [член, подписан ✓]          {m.full_name}")

        await db.commit()

    print("""
✓ Готово!

  Теперь можно демонстрировать:
    1. Войти как aliev  (пароль из seed_commission)
    2. Открыть протокол BIOT-2026-001
    3. Нажать «Подписать» → NCALayer → выбрать сертификат Алиева Абылая
    4. Протокол переходит в статус «Подписан»
    5. Четыре участника, сдавших экзамен, получают удостоверения автоматически
""")


if __name__ == "__main__":
    asyncio.run(main())
