from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DB
from app.models.organization import Organization
from app.core.exceptions import NotFoundError

router = APIRouter()


class OrganizationCreate(BaseModel):
    name: str
    short_name: Optional[str] = None
    bin: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


@router.get("")
async def list_organizations(db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Organization).order_by(Organization.name))
    return result.scalars().all()


@router.post("", status_code=201)
async def create_organization(body: OrganizationCreate, db: DB, admin: CurrentAdmin):
    org = Organization(**body.model_dump())
    db.add(org)
    await db.flush()
    return org


@router.patch("/{org_id}")
async def update_organization(org_id: UUID, data: dict, db: DB, admin: CurrentAdmin):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Organization not found")
    allowed = {"name", "short_name", "bin", "contact_email", "contact_phone", "is_active"}
    for k, v in data.items():
        if k in allowed:
            setattr(org, k, v)
    return org
