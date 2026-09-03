"""
Position normalizer service.
Strips punctuation, lowercases, removes extra spaces.
"""
import re
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def normalize_position(raw: str) -> str:
    if not raw:
        return ""
    text = raw.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)  # replace punctuation with space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def positions_match(keyword: str, normalized_position: str) -> bool:
    """Check if a rule keyword is contained in the normalized position string."""
    kw = normalize_position(keyword)
    return kw in normalized_position


async def find_course_for_position(db: AsyncSession, discipline_id: UUID, norm_position: str):
    """
    Shared by the Excel import (row_processor.py) and the "add manually"
    endpoint (batches.py) so both use the exact same matching rule: a course
    whose target_positions keyword list matches this position, falling back
    to a course with an empty target_positions ("for everyone"). Returns
    None if neither exists — the caller is then responsible for surfacing
    that to the admin, since it means the person has no course to take.
    """
    from app.models.course import Course

    result = await db.execute(
        select(Course)
        .where(Course.discipline_id == discipline_id, Course.is_active == True)  # noqa: E712
        .order_by(Course.name)
    )
    courses = result.scalars().all()
    generic = None
    for course in courses:
        tp = (course.target_positions or "").strip()
        if not tp:
            generic = course
            continue
        for kw in [k.strip() for k in tp.replace(";", ",").split(",") if k.strip()]:
            if positions_match(kw, norm_position):
                return course
    return generic
