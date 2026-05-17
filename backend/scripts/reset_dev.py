"""
Dev reset script — очищает тестовые/демо данные из локальной БД.

Удаляет (каскадом):
  • все протоколы (→ участников, членов комиссии, удостоверения)
  • всех обучаемых (learner users)
  • все учебные потоки (training_batches)
  • все организации
  • старые демо-аккаунты администраторов (chair, member1, любые demo.*)

НЕ трогает:
  • суперадминов (is_superadmin=True)
  • реальных членов комиссии (ayapbergenov, dzhajgulova, aliev)
  • training_types, courses, disciplines, tests и т.д.

Usage:
  docker compose exec backend python -m scripts.reset_dev
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text, delete
from app.core.database import AsyncSessionLocal
from app.models.user import AdminUser, User
from app.models.organization import Organization
from app.models.batch import TrainingBatch
from app.models.protocol import (
    Protocol, ProtocolCommissionMember, ProtocolParticipant
)
from app.models.certificate import Certificate
from app.models.assignment import UserCourseAssignment
from app.models.attempt import TestAttempt, TestAttemptAnswer
from app.models.import_row import ImportRow

# Логины, которые НЕЛЬЗЯ удалять
PROTECTED_LOGINS = {"ayapbergenov", "dzhajgulova", "aliev"}

# Старые демо-логины, которые нужно удалить
DEMO_ADMIN_LOGINS = {"chair", "member1"}


async def main():
    print("=== Dev reset: очистка тестовых данных ===\n")

    confirm = input("Это удалит все протоколы, обучаемых и демо-аккаунты. Продолжить? [y/N] ").strip().lower()
    if confirm != "y":
        print("Отменено.")
        return

    async with AsyncSessionLocal() as db:

        # 1. Удостоверения
        res = await db.execute(delete(Certificate))
        print(f"  удалено удостоверений:          {res.rowcount}")

        # 2. Участники протокола (FK → protocols)
        res = await db.execute(delete(ProtocolParticipant))
        print(f"  удалено участников протокола:   {res.rowcount}")

        # 3. Члены комиссии в протоколах (FK → protocols, admin_users)
        res = await db.execute(delete(ProtocolCommissionMember))
        print(f"  удалено членов комиссии:        {res.rowcount}")

        # 4. Протоколы
        res = await db.execute(delete(Protocol))
        print(f"  удалено протоколов:             {res.rowcount}")

        # 5. Ответы на попытки тестов
        res = await db.execute(delete(TestAttemptAnswer))
        print(f"  удалено ответов на тесты:       {res.rowcount}")

        # 6. Попытки тестов
        res = await db.execute(delete(TestAttempt))
        print(f"  удалено попыток тестов:         {res.rowcount}")

        # 7. Назначения курсов
        res = await db.execute(delete(UserCourseAssignment))
        print(f"  удалено назначений курсов:      {res.rowcount}")

        # 8. Строки импорта
        res = await db.execute(delete(ImportRow))
        print(f"  удалено строк импорта:          {res.rowcount}")

        # 9. Обучаемые (learners)
        res = await db.execute(delete(User))
        print(f"  удалено обучаемых:              {res.rowcount}")

        # 10. Учебные потоки
        res = await db.execute(delete(TrainingBatch))
        print(f"  удалено учебных потоков:        {res.rowcount}")

        # 11. Организации
        res = await db.execute(delete(Organization))
        print(f"  удалено организаций:            {res.rowcount}")

        # 12. Старые демо-аккаунты администраторов
        demo_deleted = 0
        for login in DEMO_ADMIN_LOGINS:
            r = await db.execute(
                delete(AdminUser).where(
                    AdminUser.login == login,
                    AdminUser.login.not_in(PROTECTED_LOGINS),
                )
            )
            demo_deleted += r.rowcount
        # На случай если есть другие demo.* аккаунты
        r = await db.execute(
            delete(AdminUser).where(
                AdminUser.login.like("demo.%"),
                AdminUser.is_superadmin == False,  # noqa: E712
                AdminUser.login.not_in(PROTECTED_LOGINS),
            )
        )
        demo_deleted += r.rowcount
        print(f"  удалено демо-аккаунтов:         {demo_deleted}")

        await db.commit()

    print("\n✓ Готово. БД очищена. Теперь запустите:")
    print("    docker compose exec backend python -m scripts.seed_demo")
    print("    docker compose exec backend python -m scripts.seed_commission  # если нужно пересоздать комиссию")


if __name__ == "__main__":
    asyncio.run(main())
