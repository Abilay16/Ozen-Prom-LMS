"""
Demo seed script — создаёт реалистичный стейт для тестирования ЭЦП.

Использует реальные аккаунты комиссии (создаются через seed_commission.py):
  Председатель: ayapbergenov  — Аяпбергенов Алпамыс Аскарұлы
  Члены:        dzhajgulova   — Джайгулова Ұлболсын Серікқызы
                aliev         — Алиев Абылай Илиясулы

Создаёт (идемпотентно):
  Организация: ТОО «КазМунайСервис» (подрядчик Озен-Пром)

  Обучаемые (5 сотрудников-подрядчика):
    dm.dusenov    / Pass1234  — Дюсенов Берик Мухтарович      (сдал)
    dm.akhmetov   / Pass1234  — Ахметов Нурлан Серікович      (сдал)
    dm.umarov     / Pass1234  — Умаров Рустам Бахтиёрович     (сдал)
    dm.smag       / Pass1234  — Смагулова Айгуль Болатовна    (сдала)
    dm.zhaksybek  / Pass1234  — Жаксыбеков Ерлан Тахирович    (не сдал)

  Протокол:
    BIOT-2026-001 — БиОТ, периодическая проверка, НА ПОДПИСИ ← готов к ЭЦП

Usage:
  docker compose exec backend python -m scripts.seed_demo

Запускать ПОСЛЕ seed_commission.py. Идемпотентен — безопасно запускать повторно.
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime, timezone
from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import AdminUser, User
from app.models.organization import Organization
from app.models.training_type import TrainingType
from app.models.protocol import (
    Protocol, ProtocolCommissionMember, ProtocolParticipant,
    ProtocolStatus, CommissionRole, ParticipantResult, CheckType,
)


# ── helpers ───────────────────────────────────────────────────────────────────

async def get_or_create_admin(db, login, password, full_name, is_superadmin=False,
                               is_commission_eligible=False, position_title=None):
    row = (await db.execute(select(AdminUser).where(AdminUser.login == login))).scalar_one_or_none()
    if row:
        print(f"  [skip] admin '{login}' already exists")
        return row
    row = AdminUser(
        login=login,
        password_hash=hash_password(password),
        full_name=full_name,
        is_superadmin=is_superadmin,
        is_commission_eligible=is_commission_eligible,
        position_title=position_title,
    )
    db.add(row)
    await db.flush()
    print(f"  [+] admin '{login}'  pw='{password}'  commission={is_commission_eligible}")
    return row


async def get_or_create_user(db, login, password, full_name, org_id, position_raw):
    row = (await db.execute(select(User).where(User.login == login))).scalar_one_or_none()
    if row:
        print(f"  [skip] user '{login}' already exists")
        return row
    row = User(
        login=login,
        password_hash=hash_password(password),
        plain_password=password,
        full_name=full_name,
        normalized_full_name=full_name.lower(),
        organization_id=org_id,
        position_raw=position_raw,
        is_active=True,
    )
    db.add(row)
    await db.flush()
    print(f"  [+] user '{login}'  pw='{password}'")
    return row


async def get_or_create_org(db, name):
    row = (await db.execute(select(Organization).where(Organization.name == name))).scalar_one_or_none()
    if row:
        print(f"  [skip] org '{name}' already exists")
        return row
    row = Organization(name=name, short_name="ОПТ", bin="111111111111")
    db.add(row)
    await db.flush()
    print(f"  [+] org '{name}'")
    return row


async def get_training_type(db, code):
    row = (await db.execute(select(TrainingType).where(TrainingType.code == code))).scalar_one_or_none()
    if not row:
        raise RuntimeError(f"TrainingType with code='{code}' not found — run migrations first")
    return row


async def protocol_exists(db, number):
    row = (await db.execute(select(Protocol).where(Protocol.protocol_number == number))).scalar_one_or_none()
    return row is not None


async def create_protocol(db, *, number, training_type, org, status,
                          exam_date, order_number, order_date,
                          check_type, chair_admin, member_admins,
                          participants):
    if await protocol_exists(db, number):
        print(f"  [skip] protocol '{number}' already exists")
        return

    proto = Protocol(
        protocol_number=number,
        training_type_id=training_type.id,
        organization_id=org.id,
        exam_date=exam_date,
        order_number=order_number,
        order_date=order_date,
        check_type=check_type,
        status=status,
    )
    db.add(proto)
    await db.flush()

    # Commission
    chair_slot = ProtocolCommissionMember(
        protocol_id=proto.id,
        admin_user_id=chair_admin.id,
        full_name=chair_admin.full_name,
        position_title=chair_admin.position_title or "Председатель комиссии",
        role=CommissionRole.chair,
        sort_order=0,
    )
    db.add(chair_slot)

    for i, adm in enumerate(member_admins):
        db.add(ProtocolCommissionMember(
            protocol_id=proto.id,
            admin_user_id=adm.id,
            full_name=adm.full_name,
            position_title=adm.position_title or "Член комиссии",
            role=CommissionRole.member,
            sort_order=i + 1,
        ))

    # Participants
    for i, (user, result, position, education) in enumerate(participants):
        db.add(ProtocolParticipant(
            protocol_id=proto.id,
            user_id=user.id if user else None,
            full_name=user.full_name if user else "—",
            organization_name=org.name,
            position=position,
            education=education,
            result=result,
            sort_order=i,
        ))

    await db.flush()

    status_label = {
        ProtocolStatus.draft: "ЧЕРНОВИК",
        ProtocolStatus.awaiting_signatures: "НА ПОДПИСИ",
        ProtocolStatus.signed: "ПОДПИСАН",
    }.get(status, str(status))
    print(f"  [+] protocol '{number}' ({status_label})")


# ── main ──────────────────────────────────────────────────────────────────────

async def main():
    print("\n═══════════════════════════════════════════════")
    print("  Ozen-Prom LMS  — Demo seed (реальная комиссия)")
    print("═══════════════════════════════════════════════\n")

    async with AsyncSessionLocal() as db:

        # ── Реальная комиссия (должна быть создана через seed_commission.py) ──
        print("▶ Загрузка аккаунтов комиссии:")
        chair = (await db.execute(
            select(AdminUser).where(AdminUser.login == "ayapbergenov")
        )).scalar_one_or_none()
        member1 = (await db.execute(
            select(AdminUser).where(AdminUser.login == "dzhajgulova")
        )).scalar_one_or_none()
        member2 = (await db.execute(
            select(AdminUser).where(AdminUser.login == "aliev")
        )).scalar_one_or_none()

        missing = [l for l, u in [("ayapbergenov", chair), ("dzhajgulova", member1), ("aliev", member2)] if not u]
        if missing:
            print(f"\n  ОШИБКА: не найдены аккаунты: {missing}")
            print("  Сначала запустите: python -m scripts.seed_commission")
            return

        print(f"  ok: {chair.full_name} (председатель)")
        print(f"  ok: {member1.full_name} (член)")
        print(f"  ok: {member2.full_name} (член)")

        # ── Organization ──────────────────────────────────────────────────────
        print("\n▶ Organization:")
        org = await get_or_create_org(db, "ТОО «КазМунайСервис»")

        # ── Learners ──────────────────────────────────────────────────────────
        print("\n▶ Learner users:")
        u1 = await get_or_create_user(db, "dm.dusenov",   "Pass1234",
                                       "Дюсенов Берик Мухтарович",       org.id, "Слесарь-ремонтник")
        u2 = await get_or_create_user(db, "dm.akhmetov",  "Pass1234",
                                       "Ахметов Нурлан Серікович",        org.id, "Оператор нефтяных скважин")
        u3 = await get_or_create_user(db, "dm.umarov",    "Pass1234",
                                       "Умаров Рустам Бахтиёрович",       org.id, "Водитель автокрана")
        u4 = await get_or_create_user(db, "dm.smag",      "Pass1234",
                                       "Смагулова Айгуль Болатовна",      org.id, "Технолог")
        u5 = await get_or_create_user(db, "dm.zhaksybek", "Pass1234",
                                       "Жаксыбеков Ерлан Тахирович",      org.id, "Электромонтёр по ремонту оборудования")

        # ── Training types ────────────────────────────────────────────────────
        print("\n▶ Training types:")
        tt_biot = await get_training_type(db, "biot")
        print("  ok: biot")

        # ── Протокол на подписи ───────────────────────────────────────────────
        print("\n▶ Protocols:")
        await create_protocol(
            db,
            number="BIOT-2026-001",
            training_type=tt_biot,
            org=org,
            status=ProtocolStatus.awaiting_signatures,
            exam_date=date(2026, 5, 13),
            order_number="ОТ-2026/38",
            order_date=date(2026, 5, 5),
            check_type=CheckType.periodic,
            chair_admin=chair,
            member_admins=[member1, member2],
            participants=[
                (u1, ParticipantResult.passed, "Слесарь-ремонтник",                       "Среднее специальное"),
                (u2, ParticipantResult.passed, "Оператор нефтяных скважин",               "Среднее специальное"),
                (u3, ParticipantResult.passed, "Водитель автокрана",                      "Среднее"),
                (u4, ParticipantResult.passed, "Технолог",                                "Высшее"),
                (u5, ParticipantResult.failed, "Электромонтёр по ремонту оборудования",   "Среднее специальное"),
            ],
        )

        await db.commit()

    print("""
═══════════════════════════════════════════════
  ГОТОВО! Демо-данные созданы.
═══════════════════════════════════════════════

  КОМИССИЯ (http://localhost:5173/admin)
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │  login          │ пароль (см. seed_commission)  │ роль в протоколе            │
  ├────────────────────────────────────────────────────────────────────────────────┤
  │  ayapbergenov   │ (создан при seed_commission)  │ Председатель                │
  │  dzhajgulova    │ (создан при seed_commission)  │ Член комиссии               │
  │  aliev          │ (создан при seed_commission)  │ Член комиссии               │
  └────────────────────────────────────────────────────────────────────────────────┘

  ОБУЧАЕМЫЕ  (5 сотрудников ТОО «КазМунайСервис»)
  ┌──────────────────────────────────────────────────────────────────────┐
  │  login         │ пароль   │ ФИО                          │ результат │
  ├──────────────────────────────────────────────────────────────────────┤
  │  dm.dusenov    │ Pass1234 │ Дюсенов Берик Мухтарович     │ сдал      │
  │  dm.akhmetov   │ Pass1234 │ Ахметов Нурлан Серікович     │ сдал      │
  │  dm.umarov     │ Pass1234 │ Умаров Рустам Бахтиёрович    │ сдал      │
  │  dm.smag       │ Pass1234 │ Смагулова Айгуль Болатовна   │ сдала     │
  │  dm.zhaksybek  │ Pass1234 │ Жаксыбеков Ерлан Тахирович   │ не сдал   │
  └──────────────────────────────────────────────────────────────────────┘

  ПРОТОКОЛ: BIOT-2026-001  — БиОТ, периодическая проверка, НА ПОДПИСИ

  СЦЕНАРИЙ ТЕСТА ЭЦП:
    1. Войти как dzhajgulova → протокол BIOT-2026-001 → «Подписать» → ЭЦП NCALayer
    2. Войти как aliev       → протокол BIOT-2026-001 → «Подписать» → ЭЦП NCALayer
    3. Войти как ayapbergenov→ протокол BIOT-2026-001 → «Подписать» → ЭЦП NCALayer
       → статус «Подписан» → удостоверения созданы автоматически (4 участника сдали)
    4. Печать протокола и удостоверений — проверить шаблон БиОТ
""")


if __name__ == "__main__":
    asyncio.run(main())

