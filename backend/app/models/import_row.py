import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import String, ForeignKey, DateTime, Enum as SAEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ImportRowStatus(str, Enum):
    ok = "ok"
    manual_review = "manual_review"
    duplicate = "duplicate"
    error = "error"


class ImportRow(Base):
    __tablename__ = "import_rows"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    row_number: Mapped[int | None] = mapped_column()   # original row in Excel
    raw_data: Mapped[dict | None] = mapped_column(JSON)         # original row as dict
    normalized_data: Mapped[dict | None] = mapped_column(JSON)  # after normalization
    status: Mapped[ImportRowStatus] = mapped_column(SAEnum(ImportRowStatus), default=ImportRowStatus.ok)
    error_message: Mapped[str | None] = mapped_column(Text)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )  # Set after user creation
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    batch: Mapped["TrainingBatch"] = relationship("TrainingBatch", back_populates="import_rows")  # noqa
    user: Mapped["User"] = relationship("User")  # noqa
