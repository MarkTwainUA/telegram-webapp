from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("chat_id", "message_id", name="uq_chat_message"),
        UniqueConstraint("idempotency_key", name="uq_idempotency"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    text: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str | None] = mapped_column(Text)
    parse_mode: Mapped[str | None] = mapped_column(String(32))
    disable_preview: Mapped[bool | None] = mapped_column()
    date: Mapped[int] = mapped_column(Integer, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    link: Mapped[str | None] = mapped_column(String(256))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
