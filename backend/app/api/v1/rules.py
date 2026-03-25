from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.rule import PositionCourseRule
from app.core.exceptions import NotFoundError

router = APIRouter()


class RuleCreate(BaseModel):
    discipline_id: UUID
    position_keyword: str
    course_id: UUID
    position_id: Optional[UUID] = None
    priority: int = 100


@router.get("")
async def list_rules(db: DB, admin: CurrentAdmin, discipline_id: Optional[UUID] = None):
    q = select(PositionCourseRule).where(PositionCourseRule.is_active == True)
    if discipline_id:
        q = q.where(PositionCourseRule.discipline_id == discipline_id)
    q = q.order_by(PositionCourseRule.priority)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", status_code=201)
async def create_rule(body: RuleCreate, db: DB, admin: CurrentAdmin):
    rule = PositionCourseRule(**body.model_dump())
    db.add(rule)
    await db.flush()
    return rule


@router.patch("/{rule_id}")
async def update_rule(rule_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(PositionCourseRule).where(PositionCourseRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Rule not found")
    allowed = {"position_keyword", "course_id", "priority", "is_active"}
    for k, v in data.items():
        if k in allowed:
            setattr(rule, k, v)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(PositionCourseRule).where(PositionCourseRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise NotFoundError("Rule not found")
    await db.delete(rule)
