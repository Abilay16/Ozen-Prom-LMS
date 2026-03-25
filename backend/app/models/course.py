import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("disciplines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_positions: Mapped[str | None] = mapped_column(String(255))  # human-readable note
    duration_hours: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    discipline: Mapped["Discipline"] = relationship("Discipline", back_populates="courses")  # noqa
    materials: Mapped[list["CourseMaterial"]] = relationship("CourseMaterial", back_populates="course")  # noqa
    test: Mapped["Test"] = relationship("Test", back_populates="course", uselist=False)  # noqa
    assignments: Mapped[list["UserCourseAssignment"]] = relationship("UserCourseAssignment", back_populates="course")  # noqa
    rules: Mapped[list["PositionCourseRule"]] = relationship("PositionCourseRule", back_populates="course")  # noqa
