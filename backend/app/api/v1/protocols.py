import uuid
from uuid import UUID
from typing import Optional
from datetime import date, datetime, timezone

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentAdmin, CurrentSuperAdmin, DB
from app.models.user import User, AdminUser
from app.models.assignment import UserCourseAssignment, AssignmentStatus
from app.models.protocol import (
    Protocol, ProtocolCommissionMember, ProtocolParticipant,
    ProtocolStatus, CommissionRole, ParticipantResult, CheckType,
)
from app.models.certificate import Certificate
from app.models.training_type import TrainingType
from app.models.organization import Organization
from app.models.batch import TrainingBatch
from app.core.exceptions import NotFoundError, ConflictError
from app.utils.cms_parser import parse_cms, CMSParseError
from app.utils.name_utils import names_match

router = APIRouter()

# ── Pydantic schemas ─────────────────────────────────────────────────────────

class CommissionMemberIn(BaseModel):
    admin_user_id: Optional[UUID] = None   # if set, full_name is pulled from AdminUser
    full_name: Optional[str] = None         # required only when admin_user_id is absent
    position_title: Optional[str] = None
    role: CommissionRole  # "chair" | "member"
    sort_order: int = 0


class CommissionMemberOut(BaseModel):
    id: UUID
    admin_user_id: Optional[UUID]
    full_name: str
    position_title: Optional[str] = None
    role: CommissionRole
    sort_order: int
    signed_at: Optional[datetime] = None
    # ЭЦП fields
    signer_cert_serial: Optional[str] = None
    signer_cert_owner: Optional[str] = None
    signer_cert_valid_from: Optional[datetime] = None
    signer_cert_valid_to: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParticipantIn(BaseModel):
    full_name: str
    organization_name: Optional[str] = None
    position: Optional[str] = None
    education: Optional[str] = None
    result: Optional[ParticipantResult] = None
    user_id: Optional[UUID] = None
    sort_order: int = 0


class ParticipantUpdate(BaseModel):
    full_name: Optional[str] = None
    organization_name: Optional[str] = None
    position: Optional[str] = None
    education: Optional[str] = None
    result: Optional[ParticipantResult] = None


class ParticipantOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    full_name: str
    organization_name: Optional[str] = None
    position: Optional[str]
    education: Optional[str]
    result: Optional[ParticipantResult]
    sort_order: int
    certificate_id: Optional[UUID] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_extended(cls, p: ProtocolParticipant):
        obj = cls.model_validate(p)
        if p.certificate:
            obj.certificate_id = p.certificate.id
        return obj


class BatchShort(BaseModel):
    id: UUID
    name: str
    organization_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ProtocolCreate(BaseModel):
    protocol_number: str
    batch_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    training_type_id: UUID
    exam_date: date
    order_number: Optional[str] = None
    order_date: Optional[date] = None
    legal_basis: Optional[str] = None
    regulatory_docs: Optional[str] = None
    check_type: Optional[CheckType] = None
    commission_members: list[CommissionMemberIn] = []
    participants: list[ParticipantIn] = []


class ProtocolUpdate(BaseModel):
    protocol_number: Optional[str] = None
    batch_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    training_type_id: Optional[UUID] = None
    exam_date: Optional[date] = None
    order_number: Optional[str] = None
    order_date: Optional[date] = None
    legal_basis: Optional[str] = None
    regulatory_docs: Optional[str] = None
    check_type: Optional[CheckType] = None
    status: Optional[ProtocolStatus] = None


class TrainingTypeShort(BaseModel):
    id: UUID
    code: str
    name_short: str
    validity_years: int

    class Config:
        from_attributes = True


class OrganizationShort(BaseModel):
    id: UUID
    name: str

    class Config:
        from_attributes = True


class ProtocolOut(BaseModel):
    id: UUID
    protocol_number: str
    batch_id: Optional[UUID]
    batch: Optional[BatchShort]
    organization_id: Optional[UUID]
    organization: Optional[OrganizationShort]
    training_type_id: Optional[UUID]
    training_type: Optional[TrainingTypeShort]
    exam_date: date
    order_number: Optional[str]
    order_date: Optional[date]
    legal_basis: Optional[str]
    regulatory_docs: Optional[str]
    check_type: Optional[CheckType] = None
    status: ProtocolStatus
    created_at: datetime
    commission_members: list[CommissionMemberOut] = []
    participants: list[ParticipantOut] = []

    class Config:
        from_attributes = True


class ProtocolListItem(BaseModel):
    id: UUID
    protocol_number: str
    training_type: Optional[TrainingTypeShort]
    organization: Optional[OrganizationShort]
    exam_date: date
    status: ProtocolStatus
    participant_count: int = 0
    passed_count: int = 0

    class Config:
        from_attributes = True


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_options():
    return (
        selectinload(Protocol.commission_members).selectinload(ProtocolCommissionMember.admin_user),
        selectinload(Protocol.participants).selectinload(ProtocolParticipant.certificate),
        selectinload(Protocol.training_type),
        selectinload(Protocol.organization),
        selectinload(Protocol.batch),
    )


async def _get_protocol_or_404(protocol_id: UUID, db) -> Protocol:
    result = await db.execute(
        select(Protocol)
        .options(*_load_options())
        .where(Protocol.id == protocol_id)
    )
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise NotFoundError("Протокол не найден")
    return protocol


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("")
async def list_protocols(
    db: DB,
    admin: CurrentAdmin,
    training_type_id: Optional[UUID] = Query(None),
    organization_id: Optional[UUID] = Query(None),
    batch_id: Optional[UUID] = Query(None),
    status: Optional[ProtocolStatus] = Query(None),
    skip: int = 0,
    limit: int = 50,
):
    q = (
        select(Protocol)
        .options(selectinload(Protocol.training_type), selectinload(Protocol.organization), selectinload(Protocol.batch))
        .order_by(Protocol.exam_date.desc())
    )
    if training_type_id:
        q = q.where(Protocol.training_type_id == training_type_id)
    if organization_id:
        q = q.where(Protocol.organization_id == organization_id)
    if batch_id:
        q = q.where(Protocol.batch_id == batch_id)
    if status:
        q = q.where(Protocol.status == status)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    protocols = result.scalars().all()

    items = []
    for p in protocols:
        items.append({
            "id": p.id,
            "protocol_number": p.protocol_number,
            "training_type": p.training_type,
            "organization": p.organization,
            "batch": p.batch,
            "exam_date": p.exam_date,
            "status": p.status,
        })
    return items


@router.get("/commission-candidates")
async def list_commission_candidates(db: DB, admin: CurrentAdmin):
    """Return admin users eligible for commission membership."""
    result = await db.execute(
        select(AdminUser)
        .where(AdminUser.is_active == True, AdminUser.is_commission_eligible == True)  # noqa
        .order_by(AdminUser.full_name)
    )
    users = result.scalars().all()
    return [
        {"id": u.id, "full_name": u.full_name, "login": u.login, "position_title": u.position_title}
        for u in users
    ]


@router.post("", status_code=201)
async def create_protocol(data: ProtocolCreate, db: DB, admin: CurrentSuperAdmin):
    protocol = Protocol(
        protocol_number=data.protocol_number,
        batch_id=data.batch_id,
        organization_id=data.organization_id,
        training_type_id=data.training_type_id,
        exam_date=data.exam_date,
        order_number=data.order_number,
        order_date=data.order_date,
        legal_basis=data.legal_basis,
        regulatory_docs=data.regulatory_docs,
        check_type=data.check_type,
        created_by_id=admin.id,
    )
    db.add(protocol)
    await db.flush()  # get protocol.id

    for i, m in enumerate(data.commission_members):
        full_name = m.full_name
        position_title = m.position_title
        if m.admin_user_id:
            res = await db.execute(select(AdminUser).where(AdminUser.id == m.admin_user_id))
            au = res.scalar_one_or_none()
            if au:
                full_name = au.full_name
                if not position_title:
                    position_title = au.position_title
        db.add(ProtocolCommissionMember(
            protocol_id=protocol.id,
            admin_user_id=m.admin_user_id,
            full_name=full_name,
            position_title=position_title,
            role=m.role,
            sort_order=m.sort_order or i,
        ))

    for i, p in enumerate(data.participants):
        db.add(ProtocolParticipant(
            protocol_id=protocol.id,
            user_id=p.user_id,
            full_name=p.full_name,
            organization_name=p.organization_name,
            position=p.position,
            education=p.education,
            result=p.result,
            sort_order=p.sort_order or i,
        ))

    protocol_id_saved = protocol.id  # save before commit (expire_on_commit safety)
    await db.commit()
    return await _get_protocol_or_404(protocol_id_saved, db)


@router.get("/{protocol_id}")
async def get_protocol(protocol_id: UUID, db: DB, admin: CurrentAdmin):
    return await _get_protocol_or_404(protocol_id, db)


@router.patch("/{protocol_id}")
async def update_protocol(protocol_id: UUID, data: ProtocolUpdate, db: DB, admin: CurrentSuperAdmin):
    protocol = await _get_protocol_or_404(protocol_id, db)
    updates = data.model_dump(exclude_unset=True)
    if protocol.status == ProtocolStatus.archived:
        raise ConflictError("Нельзя редактировать архивный протокол")
    if protocol.status in (ProtocolStatus.signed, ProtocolStatus.awaiting_signatures):
        # Only allow archiving (status-only change) on locked protocols
        if set(updates.keys()) - {'status'}:
            raise ConflictError("Нельзя редактировать протокол на подписи или подписанный")
    for field, val in updates.items():
        setattr(protocol, field, val)
    await db.commit()
    return await _get_protocol_or_404(protocol_id, db)


@router.delete("/{protocol_id}", status_code=204)
async def delete_protocol(protocol_id: UUID, db: DB, admin: CurrentSuperAdmin):
    protocol = await _get_protocol_or_404(protocol_id, db)
    await db.delete(protocol)
    await db.commit()


# ── Commission members ────────────────────────────────────────────────────────

@router.post("/{protocol_id}/commission", status_code=201)
async def add_commission_member(
    protocol_id: UUID, data: CommissionMemberIn, db: DB, admin: CurrentSuperAdmin
):
    protocol = await _get_protocol_or_404(protocol_id, db)
    if protocol.status != ProtocolStatus.draft:
        raise ConflictError("Нельзя изменять комиссию после отправки на подпись")

    full_name = data.full_name
    if data.admin_user_id:
        res = await db.execute(select(AdminUser).where(AdminUser.id == data.admin_user_id))
        au = res.scalar_one_or_none()
        if not au:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Пользователь-администратор не найден")
        full_name = au.full_name
        if not data.position_title and au.position_title:
            position_title = au.position_title
        else:
            position_title = data.position_title
    else:
        position_title = data.position_title
    if not full_name:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Необходимо указать ФИО или выбрать пользователя")

    member = ProtocolCommissionMember(
        protocol_id=protocol_id,
        admin_user_id=data.admin_user_id,
        full_name=full_name,
        position_title=position_title,
        role=data.role,
        sort_order=data.sort_order,
    )
    db.add(member)
    await db.commit()
    return await _get_protocol_or_404(protocol_id, db)


@router.delete("/{protocol_id}/commission/{member_id}", status_code=204)
async def remove_commission_member(
    protocol_id: UUID, member_id: UUID, db: DB, admin: CurrentSuperAdmin
):
    result = await db.execute(
        select(ProtocolCommissionMember).where(
            ProtocolCommissionMember.id == member_id,
            ProtocolCommissionMember.protocol_id == protocol_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundError("Член комиссии не найден")
    proto_status = await db.execute(select(Protocol.status).where(Protocol.id == protocol_id))
    if proto_status.scalar_one_or_none() != ProtocolStatus.draft:
        raise ConflictError("Нельзя изменять комиссию после отправки на подпись")
    await db.delete(member)
    await db.commit()


# ── Request signatures / Sign ─────────────────────────────────────────────────

@router.post("/{protocol_id}/request-signatures")
async def request_signatures(protocol_id: UUID, db: DB, admin: CurrentSuperAdmin):
    """Move protocol from draft → awaiting_signatures."""
    protocol = await _get_protocol_or_404(protocol_id, db)
    if protocol.status != ProtocolStatus.draft:
        raise ConflictError("Только черновик можно отправить на подпись")
    if not protocol.commission_members:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Добавьте состав комиссии перед отправкой на подпись")
    protocol.status = ProtocolStatus.awaiting_signatures
    await db.commit()
    return await _get_protocol_or_404(protocol_id, db)


class SignRequest(BaseModel):
    cms: Optional[str] = None  # Base64 CMS from NCALayer; omit for legacy (no EDS)


@router.get("/{protocol_id}/signature-payload")
async def get_signature_payload(protocol_id: UUID, db: DB, admin: CurrentAdmin):
    """
    Return the canonical string that the signer must pass to NCALayer for signing.
    Deterministic: same inputs always produce the same output.
    """
    protocol = await _get_protocol_or_404(protocol_id, db)
    # Build a stable payload from immutable protocol fields
    participant_part = "|".join(
        f"{p.full_name}:{p.result.value if p.result else 'none'}"
        for p in sorted(protocol.participants, key=lambda p: str(p.id))
    )
    payload = (
        f"PROTOCOL:{protocol.protocol_number}"
        f":{protocol.exam_date.isoformat()}"
        f":{str(protocol.id)}"
        f":{participant_part}"
    )
    return {"payload": payload}


@router.post("/{protocol_id}/sign")
async def sign_protocol(protocol_id: UUID, db: DB, admin: CurrentAdmin,
                        body: Optional[SignRequest] = None):
    """
    Current admin signs their commission slot.
    - Members (role=member) can sign at any time while awaiting_signatures.
    - Chair can sign ONLY after all members have signed → triggers status = signed.
    """
    protocol = await _get_protocol_or_404(protocol_id, db)
    if protocol.status != ProtocolStatus.awaiting_signatures:
        raise ConflictError("Протокол не находится на стадии подписания")

    # Find current admin's slot in commission
    my_slot = next(
        (m for m in protocol.commission_members if m.admin_user_id == admin.id),
        None
    )
    if not my_slot:
        raise HTTPException(status_code=403, detail="Вы не являетесь членом данной комиссии")
    if my_slot.signed_at:
        raise HTTPException(status_code=409, detail="Вы уже подписали этот протокол")

    if my_slot.role == CommissionRole.chair:
        # Chair must sign last — check all members already signed
        unsigned_members = [
            m for m in protocol.commission_members
            if m.role == CommissionRole.member and not m.signed_at
        ]
        if unsigned_members:
            names = ", ".join(m.full_name for m in unsigned_members)
            raise HTTPException(
                status_code=400,
                detail=f"Ещё не подписали: {names}"
            )

    my_slot.signed_at = datetime.now(timezone.utc)

    # Parse CMS and store certificate info if provided
    if body and body.cms:
        try:
            cert_info = parse_cms(body.cms)
        except CMSParseError as e:
            raise HTTPException(status_code=422, detail=f"Неверная ЭЦП подпись: {e}")

        # Verify the certificate belongs to the signing admin
        if not names_match(cert_info.owner, admin.full_name):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"ЭЦП не соответствует вашей учётной записи. "
                    f"В сертификате: '{cert_info.owner}', "
                    f"в системе: '{admin.full_name}'. "
                    f"Используйте ЭЦП, оформленную на ваше имя."
                ),
            )

        # Verify certificate is not expired
        now = datetime.now(timezone.utc)
        if cert_info.valid_to < now:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Сертификат ЭЦП просрочен. "
                    f"Срок действия истёк: {cert_info.valid_to.strftime('%d.%m.%Y')}."
                ),
            )

        my_slot.signature_cms = body.cms
        my_slot.signer_cert_serial = cert_info.serial
        my_slot.signer_cert_owner = cert_info.owner
        my_slot.signer_cert_valid_from = cert_info.valid_from
        my_slot.signer_cert_valid_to = cert_info.valid_to

    # Finalize: chair signed, OR everyone signed (commission has no chair)
    has_chair = any(m.role == CommissionRole.chair for m in protocol.commission_members)
    all_signed = all(m.signed_at for m in protocol.commission_members)
    if (my_slot.role == CommissionRole.chair) or (not has_chair and all_signed):
        protocol.status = ProtocolStatus.signed
        await _do_issue_certificates(protocol, db)

    await db.commit()
    protocol = await _get_protocol_or_404(protocol_id, db)
    return ProtocolOut.model_validate(protocol)


# ── Participants ──────────────────────────────────────────────────────────────

@router.post("/{protocol_id}/participants", status_code=201)
async def add_participant(
    protocol_id: UUID, data: ParticipantIn, db: DB, admin: CurrentSuperAdmin
):
    protocol = await _get_protocol_or_404(protocol_id, db)
    if protocol.status in (ProtocolStatus.signed, ProtocolStatus.awaiting_signatures):
        raise ConflictError("Протокол нельзя изменять после отправки на подпись")
    count = len(protocol.participants)
    participant = ProtocolParticipant(
        protocol_id=protocol_id,
        user_id=data.user_id,
        full_name=data.full_name,
        organization_name=data.organization_name,
        position=data.position,
        education=data.education,
        result=data.result,
        sort_order=data.sort_order or count,
    )
    db.add(participant)
    await db.commit()
    return await _get_protocol_or_404(protocol_id, db)


@router.patch("/{protocol_id}/participants/{participant_id}")
async def update_participant(
    protocol_id: UUID, participant_id: UUID, data: ParticipantUpdate,
    db: DB, admin: CurrentSuperAdmin
):
    result = await db.execute(
        select(ProtocolParticipant).where(
            ProtocolParticipant.id == participant_id,
            ProtocolParticipant.protocol_id == protocol_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("Участник не найден")
    protocol_check = await _get_protocol_or_404(protocol_id, db)
    if protocol_check.status in (ProtocolStatus.signed, ProtocolStatus.awaiting_signatures):
        raise ConflictError("Протокол нельзя изменять после отправки на подпись")
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(p, field, val)
    await db.commit()
    return await _get_protocol_or_404(protocol_id, db)


@router.delete("/{protocol_id}/participants/{participant_id}", status_code=204)
async def remove_participant(
    protocol_id: UUID, participant_id: UUID, db: DB, admin: CurrentSuperAdmin
):
    result = await db.execute(
        select(ProtocolParticipant).where(
            ProtocolParticipant.id == participant_id,
            ProtocolParticipant.protocol_id == protocol_id,
        )
    )
    p = result.scalar_one_or_none()
    if not p:
        raise NotFoundError("Участник не найден")
    protocol_check = await _get_protocol_or_404(protocol_id, db)
    if protocol_check.status in (ProtocolStatus.signed, ProtocolStatus.awaiting_signatures):
        raise ConflictError("Протокол нельзя изменять после отправки на подпись")
    await db.delete(p)
    await db.commit()


# ── Import participants from batch ────────────────────────────────────────────

@router.post("/{protocol_id}/import-participants")
async def import_participants_from_batch(protocol_id: UUID, db: DB, admin: CurrentSuperAdmin):
    """
    Импортировать участников из потока (batch), привязанного к протоколу.
    Пропускает пользователей, которые уже есть в протоколе.
    """
    protocol = await _get_protocol_or_404(protocol_id, db)

    if not protocol.batch_id:
        raise HTTPException(status_code=400, detail="Протокол не привязан к потоку")

    if protocol.status == ProtocolStatus.signed:
        raise HTTPException(status_code=409, detail="Протокол уже подписан")

    if protocol.status == ProtocolStatus.awaiting_signatures:
        raise HTTPException(status_code=409, detail="Протокол на подписи, изменение участников недоступно")

    # ── Validate: all assignments in this batch must be 'passed' ──────────────
    non_passed_result = await db.execute(
        select(User.full_name, UserCourseAssignment.status)
        .join(UserCourseAssignment, UserCourseAssignment.user_id == User.id)
        .where(
            UserCourseAssignment.batch_id == protocol.batch_id,
            UserCourseAssignment.status != AssignmentStatus.passed,
        )
    )
    non_passed_rows = non_passed_result.all()
    if non_passed_rows:
        details = ", ".join(f"{name} ({status.value})" for name, status in non_passed_rows[:3])
        raise HTTPException(
            status_code=409,
            detail=f"Не все участники потока завершили обучение: {details}",
        )

    # Distinct users assigned to this batch
    result = await db.execute(
        select(User)
        .join(UserCourseAssignment, UserCourseAssignment.user_id == User.id)
        .where(UserCourseAssignment.batch_id == protocol.batch_id)
        .distinct()
        .options(selectinload(User.position))
    )
    batch_users = result.scalars().all()

    # Users already in the protocol
    existing_user_ids = {p.user_id for p in protocol.participants if p.user_id}

    # Resolve organization name from protocol → batch → org
    org_name = None
    org_id = protocol.organization_id
    if not org_id and protocol.batch_id:
        batch_res = await db.execute(select(TrainingBatch).where(TrainingBatch.id == protocol.batch_id))
        batch = batch_res.scalar_one_or_none()
        if batch:
            org_id = batch.organization_id
    if org_id:
        org_res = await db.execute(select(Organization).where(Organization.id == org_id))
        org = org_res.scalar_one_or_none()
        org_name = org.name if org else None

    added = []
    for i, user in enumerate(batch_users):
        if user.id in existing_user_ids:
            continue
        position_str = user.position_raw or (user.position.name if user.position else None)
        db.add(ProtocolParticipant(
            protocol_id=protocol_id,
            user_id=user.id,
            full_name=user.full_name,
            organization_name=org_name,
            position=position_str,
            sort_order=len(protocol.participants) + i,
        ))
        added.append(user.full_name)

    await db.commit()
    protocol = await _get_protocol_or_404(protocol_id, db)
    return {"added": len(added), "names": added, "protocol": ProtocolOut.model_validate(protocol)}


async def _do_issue_certificates(protocol: Protocol, db) -> tuple[list[str], list[str]]:
    """
    Issue certificates for all participants whose result=passed and who have no cert yet.
    Returns (issued_names, skipped_participant_ids).
    Does NOT commit — caller is responsible.
    """
    # Load training type for validity period
    tt_result = await db.execute(
        select(TrainingType).where(TrainingType.id == protocol.training_type_id)
    )
    training_type = tt_result.scalar_one_or_none()
    validity_years = training_type.validity_years if training_type else 1

    # Load organization name (from protocol or batch)
    org_name = None
    org_id = protocol.organization_id
    if not org_id and protocol.batch_id:
        batch_result = await db.execute(
            select(TrainingBatch).where(TrainingBatch.id == protocol.batch_id)
        )
        batch = batch_result.scalar_one_or_none()
        if batch:
            org_id = batch.organization_id
    if org_id:
        org_result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org_result.scalar_one_or_none()
        org_name = org.name if org else None

    issued: list[str] = []
    skipped: list[str] = []

    for participant in protocol.participants:
        if participant.result != ParticipantResult.passed:
            continue
        if participant.certificate:
            skipped.append(str(participant.id))
            continue

        code = training_type.name_short.upper().replace(" ", "") if training_type else "CERT"
        date_str = protocol.exam_date.strftime("%Y%m%d")
        seq = str(uuid.uuid4().int)[:4]
        cert_number = f"{code}-{date_str}-{seq}"

        issued_date = protocol.exam_date
        try:
            valid_until = issued_date.replace(year=issued_date.year + validity_years)
        except ValueError:
            valid_until = issued_date.replace(year=issued_date.year + validity_years, day=28)

        cert = Certificate(
            certificate_number=cert_number,
            user_id=participant.user_id,
            protocol_id=protocol.id,
            participant_id=participant.id,
            training_type_id=protocol.training_type_id,
            full_name=participant.full_name,
            organization_name=org_name,
            position=participant.position,
            issued_date=issued_date,
            valid_until=valid_until,
        )
        db.add(cert)
        issued.append(participant.full_name)

    return issued, skipped


# ── Issue certificates ────────────────────────────────────────────────────────

@router.post("/{protocol_id}/issue-certificates")
async def issue_certificates(protocol_id: UUID, db: DB, admin: CurrentSuperAdmin):
    """
    Выдать удостоверения всем участникам со статусом 'passed', у которых ещё нет удостоверения.
    Только для подписанных протоколов.
    """
    protocol = await _get_protocol_or_404(protocol_id, db)
    if protocol.status != ProtocolStatus.signed:
        raise HTTPException(status_code=400, detail="Удостоверения можно выдавать только по подписанному протоколу")

    issued, skipped = await _do_issue_certificates(protocol, db)
    await db.commit()
    return {"issued": issued, "skipped_already_issued": skipped}
