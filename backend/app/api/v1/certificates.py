import uuid
from uuid import UUID
from typing import Optional
from datetime import date, datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, CurrentSuperAdmin, CurrentLearner, DB
from app.models.certificate import Certificate
from app.models.training_type import TrainingType
from app.models.user import User
from app.models.protocol import Protocol, ProtocolCommissionMember
from app.core.exceptions import NotFoundError

router = APIRouter()          # mounted at /admin/certificates
learner_router = APIRouter()  # mounted at /learner/certificates
public_router = APIRouter()   # mounted at / (no prefix)


# ── Schemas ───────────────────────────────────────────────────────────────────

class TrainingTypeShort(BaseModel):
    id: UUID
    code: str
    name_short: str
    validity_years: int

    class Config:
        from_attributes = True


class CertificateOut(BaseModel):
    id: UUID
    certificate_number: str
    user_id: Optional[UUID]
    protocol_id: Optional[UUID]
    full_name: str
    organization_name: Optional[str]
    position: Optional[str]
    training_type: Optional[TrainingTypeShort]
    issued_date: date
    valid_until: Optional[date]
    is_renewal: bool
    pdf_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CertificateCreate(BaseModel):
    certificate_number: str
    user_id: Optional[UUID] = None
    protocol_id: Optional[UUID] = None
    participant_id: Optional[UUID] = None
    training_type_id: Optional[UUID] = None
    full_name: str
    organization_name: Optional[str] = None
    position: Optional[str] = None
    issued_date: date
    valid_until: Optional[date] = None
    is_renewal: bool = False


class CertificateUpdate(BaseModel):
    certificate_number: Optional[str] = None
    full_name: Optional[str] = None
    organization_name: Optional[str] = None
    position: Optional[str] = None
    issued_date: Optional[date] = None
    valid_until: Optional[date] = None


# ── Admin routes ──────────────────────────────────────────────────────────────

@router.get("")
async def list_certificates(
    db: DB,
    admin: CurrentAdmin,
    user_id: Optional[UUID] = Query(None),
    training_type_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
):
    q = (
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .order_by(Certificate.issued_date.desc())
    )
    if user_id:
        q = q.where(Certificate.user_id == user_id)
    if training_type_id:
        q = q.where(Certificate.training_type_id == training_type_id)
    if search:
        q = q.where(Certificate.full_name.ilike(f"%{search}%"))
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", status_code=201, response_model=CertificateOut)
async def create_certificate(data: CertificateCreate, db: DB, admin: CurrentSuperAdmin):
    from app.core.exceptions import ConflictError
    existing = await db.execute(
        select(Certificate).where(Certificate.certificate_number == data.certificate_number)
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Удостоверение с таким номером уже существует")
    cert = Certificate(**data.model_dump())
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return cert


@router.get("/{cert_id}", response_model=CertificateOut)
async def get_certificate(cert_id: UUID, db: DB, admin: CurrentAdmin):
    result = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .where(Certificate.id == cert_id)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise NotFoundError("Удостоверение не найдено")
    return cert


@router.patch("/{cert_id}", response_model=CertificateOut)
async def update_certificate(cert_id: UUID, data: CertificateUpdate, db: DB, admin: CurrentSuperAdmin):
    result = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .where(Certificate.id == cert_id)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise NotFoundError("Удостоверение не найдено")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(cert, field, val)
    await db.commit()
    await db.refresh(cert)
    return cert


@router.delete("/{cert_id}", status_code=204)
async def delete_certificate(cert_id: UUID, db: DB, admin: CurrentSuperAdmin):
    result = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = result.scalar_one_or_none()
    if not cert:
        raise NotFoundError("Удостоверение не найдено")
    await db.delete(cert)
    await db.commit()


# ── Learner route ─────────────────────────────────────────────────────────────

@learner_router.get("")
async def my_certificates(db: DB, learner: CurrentLearner):
    result = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .where(Certificate.user_id == learner.id)
        .order_by(Certificate.issued_date.desc())
    )
    return result.scalars().all()


@learner_router.get("/{cert_id}", response_model=CertificateOut)
async def my_certificate_detail(cert_id: UUID, db: DB, learner: CurrentLearner):
    result = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .where(Certificate.id == cert_id, Certificate.user_id == learner.id)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise NotFoundError("Удостоверение не найдено")
    return cert


# ── Public verification ───────────────────────────────────────────────────────

def _cert_status(valid_until: date | None) -> str:
    if not valid_until:
        return "active"
    today = date.today()
    delta = (valid_until - today).days
    if delta < 0:
        return "expired"
    if delta < 30:
        return "expiring_soon"
    return "active"


@public_router.get("/verify/worker/{token}")
async def verify_worker(token: uuid.UUID, db: DB):
    """Public worker card — all certificates for one worker by verify_token."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.organization))
        .where(User.verify_token == token, User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("Карточка работника не найдена")

    certs_q = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .where(Certificate.user_id == user.id)
        .order_by(Certificate.issued_date.desc())
    )
    certs = certs_q.scalars().all()

    return {
        "full_name": user.full_name,
        "organization_name": user.organization.name if user.organization else None,
        "position": user.position_raw,
        "photo_url": f"/api/v1/users/{user.id}/photo" if user.photo_path else None,
        "certificates": [
            {
                "id": c.id,
                "certificate_number": c.certificate_number,
                "training_type_name": c.training_type.name_short if c.training_type else None,
                "training_type_code": c.training_type.code if c.training_type else None,
                "issued_date": c.issued_date,
                "valid_until": c.valid_until,
                "status": _cert_status(c.valid_until),
            }
            for c in certs
        ],
    }


@public_router.get("/verify/{cert_id}")
async def verify_certificate(cert_id: UUID, db: DB):
    result = await db.execute(
        select(Certificate)
        .options(selectinload(Certificate.training_type))
        .where(Certificate.id == cert_id)
    )
    cert = result.scalar_one_or_none()
    if not cert:
        raise NotFoundError("Удостоверение не найдено или недействительно")

    # Load protocol + commission signatures
    protocol_number = None
    signers = []
    if cert.protocol_id:
        proto_q = await db.execute(
            select(Protocol)
            .options(selectinload(Protocol.commission_members))
            .where(Protocol.id == cert.protocol_id)
        )
        proto = proto_q.scalar_one_or_none()
        if proto:
            protocol_number = proto.protocol_number
            signers = [
                {
                    "full_name": m.full_name,
                    "role": m.role.value,
                    "cert_owner": m.signer_cert_owner,
                    "signed_at": m.signed_at.isoformat() if m.signed_at else None,
                }
                for m in proto.commission_members
                if m.signed_at
            ]

    status = _cert_status(cert.valid_until)

    # Load photo_path to know if a photo exists
    photo_url = None
    if cert.user_id:
        user_q = await db.execute(select(User).where(User.id == cert.user_id))
        cert_user = user_q.scalar_one_or_none()
        if cert_user and cert_user.photo_path:
            photo_url = f"/api/v1/users/{cert.user_id}/photo"

    return {
        "id": cert.id,
        "status": status,
        "valid": status != "expired",
        "certificate_number": cert.certificate_number,
        "full_name": cert.full_name,
        "organization_name": cert.organization_name,
        "position": cert.position,
        "training_type": cert.training_type.name_ru if cert.training_type else None,
        "training_type_short": cert.training_type.name_short if cert.training_type else None,
        "training_type_code": cert.training_type.code if cert.training_type else None,
        "issued_date": cert.issued_date,
        "valid_until": cert.valid_until,
        "protocol_number": protocol_number,
        "signers": signers,
        "user_id": cert.user_id,
        "photo_url": photo_url,
    }
