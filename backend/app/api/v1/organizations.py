from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentSuperAdmin, CurrentViewerAdmin, DB, org_scope_id
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
async def list_organizations(db: DB, admin: CurrentViewerAdmin):
    stmt = select(Organization).order_by(Organization.name)
    # Наблюдатель организации видит только свою организацию.
    org_id = org_scope_id(admin)
    if org_id:
        stmt = stmt.where(Organization.id == org_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", status_code=201)
async def create_organization(body: OrganizationCreate, db: DB, admin: CurrentSuperAdmin):
    org = Organization(**body.model_dump())
    db.add(org)
    await db.flush()
    return org


@router.patch("/{org_id}")
async def update_organization(org_id: UUID, data: dict, db: DB, admin: CurrentSuperAdmin):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise NotFoundError("Организация не найдена")
    allowed = {"name", "short_name", "bin", "contact_email", "contact_phone", "is_active"}
    for k, v in data.items():
        if k in allowed:
            setattr(org, k, v)
    return org
