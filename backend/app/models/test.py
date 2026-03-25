import uuid
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    pass_score: Mapped[int] = mapped_column(Integer, default=70)       # percentage
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)      # 0 = unlimited
    time_limit_minutes: Mapped[int] = mapped_column(Integer, default=0)  # 0 = no limit
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    course: Mapped["Course"] = relationship("Course", back_populates="test")  # noqa
    questions: Mapped[list["TestQuestion"]] = relationship(
        "TestQuestion", back_populates="test", order_by="TestQuestion.sort_order"
    )
    attempts: Mapped[list["TestAttempt"]] = relationship("TestAttempt", back_populates="test")  # noqa


class TestQuestion(Base):
    __tablename__ = "test_questions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    test_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(512))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    test: Mapped["Test"] = relationship("Test", back_populates="questions")  # noqa
    options: Mapped[list["TestQuestionOption"]] = relationship(
        "TestQuestionOption", back_populates="question", order_by="TestQuestionOption.sort_order"
    )


class TestQuestionOption(Base):
    __tablename__ = "test_question_options"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("test_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped["TestQuestion"] = relationship("TestQuestion", back_populates="options")  # noqa
