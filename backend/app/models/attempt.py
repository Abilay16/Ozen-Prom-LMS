import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import ForeignKey, DateTime, Integer, Boolean, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttemptStatus(str, Enum):
    in_progress = "in_progress"
    completed = "completed"
    timed_out = "timed_out"


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_course_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[AttemptStatus] = mapped_column(SAEnum(AttemptStatus), default=AttemptStatus.in_progress)
    score: Mapped[int | None] = mapped_column(Integer)       # correct answers count
    max_score: Mapped[int | None] = mapped_column(Integer)   # total questions
    score_percent: Mapped[int | None] = mapped_column(Integer)
    passed: Mapped[bool | None] = mapped_column(Boolean)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="attempts")  # noqa
    assignment: Mapped["UserCourseAssignment"] = relationship("UserCourseAssignment", back_populates="attempts")  # noqa
    test: Mapped["Test"] = relationship("Test", back_populates="attempts")  # noqa
    answers: Mapped[list["TestAttemptAnswer"]] = relationship("TestAttemptAnswer", back_populates="attempt")  # noqa


class TestAttemptAnswer(Base):
    __tablename__ = "test_attempt_answers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("test_questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("test_question_options.id", ondelete="SET NULL")
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean)

    attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="answers")  # noqa
