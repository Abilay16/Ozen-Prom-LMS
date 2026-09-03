import uuid
from datetime import date

from sqlalchemy import String, Boolean, Integer, Date, Text
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

    # Defaults used to prefill a new protocol's order_number/order_date/legal_basis
    # when this training type is picked (still editable afterwards, and never
    # touched on an existing protocol).
    default_order_number: Mapped[str | None] = mapped_column(String(100))
    default_order_date: Mapped[date | None] = mapped_column(Date)
    default_legal_basis: Mapped[str | None] = mapped_column(Text)
