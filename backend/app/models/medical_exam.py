import uuid
from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, Date, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MedicalExam(Base):
    """Запись о прохождении медицинского осмотра (периодический / предварительный).

    Данные импортируются из сводной таблицы Excel, которую присылает клиника.
    """
    __tablename__ = "medical_exams"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Привязка к пользователю (может быть NULL если работник не найден в системе)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Данные из Excel-файла клиники
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)       # муж / жен
    workplace: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)   # Объект/участок
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)    # Занимаемая должность
    icd10_group: Mapped[Optional[str]] = mapped_column(Text, nullable=True)        # МКБ-10 / группа диспансерного
    fit_for_work: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)   # Профпри годен к работам
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)         # Дата прохождения

    # Откуда импортировано
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # имя загруженного файла
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped[Optional["User"]] = relationship("User")  # noqa
    organization: Mapped[Optional["Organization"]] = relationship("Organization")  # noqa
