import uuid
from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Discipline(Base):
    __tablename__ = "disciplines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)  # e.g. "BIOT", "PTM"
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "БиОТ"
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="discipline")  # noqa
    rules: Mapped[list["PositionCourseRule"]] = relationship("PositionCourseRule", back_populates="discipline")  # noqa
