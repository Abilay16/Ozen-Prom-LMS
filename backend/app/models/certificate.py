import uuid
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Certificate(Base):
    """
    Placeholder for future certificate/удостоверение feature.
    Not used on MVP — table exists to avoid schema rework later.
    """
    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_course_assignments.id", ondelete="CASCADE"), nullable=False
    )
    certificate_number: Mapped[str | None] = mapped_column(String(100), unique=True)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_path: Mapped[str | None] = mapped_column(String(512))  # PDF path when generated
