import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AssignmentStatus(str, Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    passed = "passed"
    failed = "failed"


class UserCourseAssignment(Base):
    __tablename__ = "user_course_assignments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), nullable=False
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_batches.id", ondelete="SET NULL"), index=True
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        SAEnum(AssignmentStatus), default=AssignmentStatus.assigned
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="assignments")  # noqa
    course: Mapped["Course"] = relationship("Course", back_populates="assignments")  # noqa
    discipline: Mapped["Discipline"] = relationship("Discipline")  # noqa
    batch: Mapped["TrainingBatch"] = relationship("TrainingBatch", back_populates="assignments")  # noqa
    attempts: Mapped[list["TestAttempt"]] = relationship("TestAttempt", back_populates="assignment")  # noqa
