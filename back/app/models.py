from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    # Stocké sans fuseau (MySQL DATETIME), toujours en UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invited_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    invited_by: Mapped["User | None"] = relationship(remote_side=[id])


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    # Optionnel : réserve l'invitation à une adresse précise.
    email: Mapped[str | None] = mapped_column(String(255))
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    used_by: Mapped[User | None] = relationship(foreign_keys=[used_by_id])

    @property
    def status(self) -> str:
        if self.revoked:
            return "revoked"
        if self.used_at is not None:
            return "used"
        if self.expires_at <= utcnow():
            return "expired"
        return "pending"


class Comedian(Base):
    """Une chaîne YouTube suivie. `subscribed` : sa synchronisation périodique est active."""

    __tablename__ = "comedians"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    youtube_channel_id: Mapped[str] = mapped_column(String(32), unique=True)
    channel_url: Mapped[str] = mapped_column(String(300))
    subscribed: Mapped[bool] = mapped_column(Boolean, default=True)
    # Filtre : seuls les sketchs dont la durée est dans [min, max] sont retenus.
    min_duration_s: Mapped[int] = mapped_column(Integer, default=120)
    max_duration_s: Mapped[int] = mapped_column(Integer, default=1800)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    sketches: Mapped[list["Sketch"]] = relationship(back_populates="comedian", cascade="all, delete-orphan")


class Sketch(Base):
    __tablename__ = "sketches"
    __table_args__ = (Index("ix_sketches_comedian_published", "comedian_id", "published_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    comedian_id: Mapped[int] = mapped_column(ForeignKey("comedians.id", ondelete="CASCADE"))
    youtube_id: Mapped[str] = mapped_column(String(16), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    duration_s: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime] = mapped_column(DateTime)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    # discovered | filtered (hors filtre de durée). Les états "gardé" arrivent avec le téléchargement.
    status: Mapped[str] = mapped_column(String(16), default="discovered")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    comedian: Mapped[Comedian] = relationship(back_populates="sketches")
