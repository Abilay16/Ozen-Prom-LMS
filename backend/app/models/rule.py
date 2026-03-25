import uuid
from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PositionCourseRule(Base):
    """Rule: discipline + position_keyword → course."""
    __tablename__ = "position_course_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("disciplines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("positions.id", ondelete="SET NULL")
    )
    position_keyword: Mapped[str] = mapped_column(String(255), nullable=False)  # normalized keyword for matching
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, default=100)  # lower = higher priority
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    discipline: Mapped["Discipline"] = relationship("Discipline", back_populates="rules")  # noqa
    position: Mapped["Position"] = relationship("Position", back_populates="rules")  # noqa
    course: Mapped["Course"] = relationship("Course", back_populates="rules")  # noqa
