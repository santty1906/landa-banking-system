"""Persistence model for encrypted face embeddings."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class FaceEmbedding(Base):
    """Stores one active encrypted facial embedding per user for MVP."""

    __tablename__ = "face_embeddings"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    encrypted_embedding: Mapped[str] = mapped_column(String, nullable=False)
    encryption_metadata: Mapped[dict] = mapped_column(JSON, nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
