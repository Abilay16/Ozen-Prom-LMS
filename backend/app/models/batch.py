import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BatchStatus(str, Enum):
    draft = "draft"
    processing = "processing"
    completed = "completed"
    archived = "archived"


class TrainingBatch(Base):
    __tablename__ = "training_batches"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[BatchStatus] = mapped_column(
        SAEnum(BatchStatus), default=BatchStatus.draft
    )
    excel_file_path: Mapped[str | None] = mapped_column(String(512))
    notes: Mapped[str | None] = mapped_column(Text)
    # List of discipline UUID strings selected for this batch
    discipline_ids: Mapped[list | None] = mapped_column(JSON, default=list)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("admin_users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="batches")  # noqa
    import_rows: Mapped[list["ImportRow"]] = relationship("ImportRow", back_populates="batch")  # noqa
    assignments: Mapped[list["UserCourseAssignment"]] = relationship("UserCourseAssignment", back_populates="batch")  # noqa
