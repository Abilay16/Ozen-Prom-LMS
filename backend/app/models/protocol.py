import uuid
import enum
from datetime import datetime, timezone, date

from sqlalchemy import String, ForeignKey, DateTime, Date, Text, Integer
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.core.database import Base


class ProtocolStatus(str, enum.Enum):
    draft = "draft"
    awaiting_signatures = "awaiting_signatures"
    signed = "signed"
    archived = "archived"


class CheckType(str, enum.Enum):
    primary = "первичный"
    periodic = "периодический"
    repeat = "повторный"
    unplanned = "внеплановый"


class CommissionRole(str, enum.Enum):
    chair = "chair"
    member = "member"


class ParticipantResult(str, enum.Enum):
    passed = "passed"
    failed = "failed"


class Protocol(Base):
    """Протокол проверки знаний (БиОТ / ПТМ / ПромБез и т.д.)"""
    __tablename__ = "protocols"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    protocol_number: Mapped[str] = mapped_column(String(50), nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_batches.id", ondelete="SET NULL"), index=True
    )
    training_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_types.id", ondelete="SET NULL")
    )
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    order_number: Mapped[str | None] = mapped_column(String(100))
    order_date: Mapped[date | None] = mapped_column(Date)
    legal_basis: Mapped[str | None] = mapped_column(Text)
    regulatory_docs: Mapped[str | None] = mapped_column(Text)  # \n-separated list
    check_type: Mapped[Optional["CheckType"]] = mapped_column(
        SAEnum(CheckType, name="checktype"), nullable=True
    )
    status: Mapped[ProtocolStatus] = mapped_column(
        SAEnum(ProtocolStatus, name="protocolstatus"), default=ProtocolStatus.draft
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    training_type: Mapped["TrainingType"] = relationship("TrainingType", lazy="joined")  # noqa
    organization: Mapped["Organization"] = relationship("Organization")  # noqa
    batch: Mapped["TrainingBatch"] = relationship("TrainingBatch")  # noqa
    commission_members: Mapped[list["ProtocolCommissionMember"]] = relationship(
        "ProtocolCommissionMember", back_populates="protocol",
        cascade="all, delete-orphan", order_by="ProtocolCommissionMember.sort_order"
    )
    participants: Mapped[list["ProtocolParticipant"]] = relationship(
        "ProtocolParticipant", back_populates="protocol",
        cascade="all, delete-orphan", order_by="ProtocolParticipant.sort_order"
    )


class ProtocolCommissionMember(Base):
    """Член комиссии в протоколе (председатель или рядовой член)."""
    __tablename__ = "protocol_commission_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    protocol_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False, index=True
    )
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL"), index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    position_title: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[CommissionRole] = mapped_column(SAEnum(CommissionRole, name="commissionrole"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ЭЦП (NCALayer CMS signature)
    signature_cms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)           # Base64 CMS/PKCS#7
    signer_cert_serial: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # hex serial
    signer_cert_owner: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)   # ФИО из CN
    signer_cert_valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    signer_cert_valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    protocol: Mapped["Protocol"] = relationship("Protocol", back_populates="commission_members")
    admin_user: Mapped[Optional["AdminUser"]] = relationship("AdminUser", foreign_keys=[admin_user_id])  # noqa


class ProtocolParticipant(Base):
    """Участник проверки знаний (сотрудник организации)."""
    __tablename__ = "protocol_participants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    protocol_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    position: Mapped[str | None] = mapped_column(String(255))
    education: Mapped[str | None] = mapped_column(String(100))
    result: Mapped[ParticipantResult | None] = mapped_column(
        SAEnum(ParticipantResult, name="participantresult")
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    protocol: Mapped["Protocol"] = relationship("Protocol", back_populates="participants")
    certificate: Mapped["Certificate"] = relationship(  # noqa
        "Certificate", back_populates="participant", uselist=False
    )

    @property
    def certificate_id(self):
        """Convenience property so Pydantic from_attributes can read certificate.id."""
        return self.certificate.id if self.certificate else None
