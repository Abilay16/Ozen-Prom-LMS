"""
Assignment engine service.
Given a discipline_id and normalized position string,
finds the best matching course via position_course_rules.
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.rule import PositionCourseRule
from app.services.positions.normalizer import positions_match


class AssignmentEngineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_course(self, discipline_id: UUID, normalized_position: str) -> UUID | None:
        """
        Returns course_id if a matching rule is found, else None.
        Rules are ordered by priority (ascending = higher priority).
        """
        result = await self.db.execute(
            select(PositionCourseRule)
            .where(
                PositionCourseRule.discipline_id == discipline_id,
                PositionCourseRule.is_active == True,
            )
            .order_by(PositionCourseRule.priority)
        )
        rules = result.scalars().all()

        for rule in rules:
            if positions_match(rule.position_keyword, normalized_position):
                return rule.course_id

        return None
