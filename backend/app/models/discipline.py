import uuid
from sqlalchemy import String, Boolean, Text, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Discipline(Base):
    __tablename__ = "disciplines"
    # Код уникален только среди действующих: архивная дисциплина не мешает
    # завести новую с тем же кодом (миграция 0009).
    __table_args__ = (
        Index("uq_disciplines_code_active", "code", unique=True, postgresql_where=text("is_active")),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "BIOT", "PTM"
    name: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "БиОТ"
    description: Mapped[str | None] = mapped_column(Text)
    # False = в архиве: не предлагается для новых потоков, но история и
    # назначения сотрудников остаются.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="discipline")  # noqa
    rules: Mapped[list["PositionCourseRule"]] = relationship("PositionCourseRule", back_populates="discipline")  # noqa
