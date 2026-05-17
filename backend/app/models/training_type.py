import uuid

from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TrainingType(Base):
    """Тип проверки знаний: БиОТ, ПТМ, ПромБез и т.д."""
    __tablename__ = "training_types"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_ru: Mapped[str] = mapped_column(String(255), nullable=False)
    name_short: Mapped[str] = mapped_column(String(50), nullable=False)
    validity_years: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
