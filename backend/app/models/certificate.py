import uuid
from datetime import datetime, timezone, date

from sqlalchemy import String, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Certificate(Base):
    """Удостоверение о проверке знаний."""
    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    certificate_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    protocol_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("protocols.id", ondelete="SET NULL")
    )
    participant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("protocol_participants.id", ondelete="SET NULL")
    )
    training_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_types.id", ondelete="SET NULL")
    )
    # Denormalized fields for PDF rendering
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_name: Mapped[str | None] = mapped_column(String(255))
    position: Mapped[str | None] = mapped_column(String(255))
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)
    is_renewal: Mapped[bool] = mapped_column(Boolean, default=False)
    pdf_path: Mapped[str | None] = mapped_column(String(512))
    qr_code_path: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    training_type: Mapped["TrainingType"] = relationship("TrainingType", lazy="joined")  # noqa
    participant: Mapped["ProtocolParticipant"] = relationship(  # noqa
        "ProtocolParticipant", back_populates="certificate"
    )
