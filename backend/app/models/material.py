import uuid
from enum import Enum
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, Integer, DateTime, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MaterialType(str, Enum):
    video_file = "video_file"
    video_url = "video_url"
    pdf = "pdf"
    docx = "docx"
    image = "image"
    external_link = "external_link"


class CourseMaterial(Base):
    __tablename__ = "course_materials"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[MaterialType] = mapped_column(SAEnum(MaterialType), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(512))   # local path for files
    url: Mapped[str | None] = mapped_column(Text)                 # for URLs/embeds
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    course: Mapped["Course"] = relationship("Course", back_populates="materials")  # noqa
