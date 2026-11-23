"""
Постраничная выдача списков.

Общее количество отдаётся заголовком X-Total-Count — тело ответа остаётся
обычным массивом, поэтому существующие вызовы API не ломаются. Раньше списки
молча обрезались на 50/500 записях, и админ не видел остальное.
"""
from fastapi import Response
from sqlalchemy import func, select

# Верхняя граница одной страницы (часть экранов грузит списки целиком для
# выпадающих списков — 2000 с запасом покрывает текущие объёмы).
MAX_LIMIT = 2000


async def paged(db, q, response: Response, skip: int, limit: int, *, scalars: bool = True):
    skip = max(0, skip)
    limit = max(1, min(limit, MAX_LIMIT))
    total = (await db.execute(select(func.count()).select_from(q.order_by(None).subquery()))).scalar_one()
    response.headers["X-Total-Count"] = str(total)
    result = await db.execute(q.offset(skip).limit(limit))
    return result.scalars().all() if scalars else result.all()
