import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Learner — employee of a client organization."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    verify_token: Mapped[uuid.UUID | None] = mapped_column(
        default=uuid.uuid4, unique=True, index=True, nullable=True,
        server_default=text("gen_random_uuid()")
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_full_name: Mapped[str] = mapped_column(String(255), index=True)

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("positions.id", ondelete="SET NULL")
    )
    position_raw: Mapped[str | None] = mapped_column(String(255))  # original from Excel
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("training_batches.id", ondelete="SET NULL")
    )  # First import batch

    plain_password: Mapped[str | None] = mapped_column(String(255))  # stored for admin reference
    photo_path: Mapped[str | None] = mapped_column(String(512))  # path to uploaded photo
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    # passive_deletes=True on the two CASCADE children below tells SQLAlchemy
    # to trust the DB's own ON DELETE CASCADE (see ondelete="CASCADE" on their
    # user_id column) instead of loading every assignment/attempt into the
    # session to null out a NOT NULL FK itself — without this, deleting a
    # user raises an IntegrityError (NOT NULL violation) at flush time.
    organization: Mapped["Organization"] = relationship("Organization", back_populates="users")  # noqa
    position: Mapped["Position"] = relationship("Position")  # noqa
    assignments: Mapped[list["UserCourseAssignment"]] = relationship(
        "UserCourseAssignment", back_populates="user", passive_deletes=True
    )  # noqa
    attempts: Mapped[list["TestAttempt"]] = relationship(
        "TestAttempt", back_populates="user", passive_deletes=True
    )  # noqa


class AdminUser(Base):
    """Ozen-Prom administrator."""
    __tablename__ = "admin_users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_commission_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default_chair: Mapped[bool] = mapped_column(Boolean, default=False)  # auto-picked as chair on new protocols
    position_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
