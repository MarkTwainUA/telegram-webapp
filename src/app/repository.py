from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Post


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_post(
        self,
        *,
        chat_id: str,
        message_id: int,
        text: str | None,
        caption: str | None,
        parse_mode: str | None,
        disable_preview: bool | None,
        date: int,
        username: str | None,
        link: str | None,
        idempotency_key: str | None = None,
    ) -> Post:
        existing = None
        if idempotency_key:
            existing = await self.get_by_idempotency_key(idempotency_key)
        if existing is None:
            existing = await self.get_by_chat_and_message(chat_id, message_id)
        if existing:
            existing.text = text
            existing.caption = caption
            existing.parse_mode = parse_mode
            existing.disable_preview = disable_preview
            existing.date = date
            existing.username = username
            existing.link = link
            existing.idempotency_key = idempotency_key or existing.idempotency_key
            await self.session.flush()
            return existing
        post = Post(
            chat_id=str(chat_id),
            message_id=message_id,
            text=text,
            caption=caption,
            parse_mode=parse_mode,
            disable_preview=disable_preview,
            date=date,
            username=username,
            link=link,
            idempotency_key=idempotency_key,
        )
        self.session.add(post)
        await self.session.flush()
        return post

    async def get_by_idempotency_key(self, key: str) -> Optional[Post]:
        stmt = select(Post).where(Post.idempotency_key == key)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_chat_and_message(self, chat_id: str, message_id: int) -> Optional[Post]:
        stmt = select(Post).where(Post.chat_id == str(chat_id), Post.message_id == message_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete_by_chat_and_message(self, chat_id: str, message_id: int) -> int:
        stmt = delete(Post).where(Post.chat_id == str(chat_id), Post.message_id == message_id)
        res = await self.session.execute(stmt)
        return res.rowcount or 0

    async def list_posts(self, chat_id: str, limit: int, offset: int) -> tuple[list[Post], int]:
        stmt = (
            select(Post)
            .where(Post.chat_id == str(chat_id))
            .order_by(Post.date.desc())
            .offset(offset)
            .limit(limit)
        )
        items_res = await self.session.execute(stmt)
        items = list(items_res.scalars().all())
        # total count (simple approach for SQLite without count(*))
        count_stmt = select(Post).where(Post.chat_id == str(chat_id))
        count_res = await self.session.execute(count_stmt)
        total = len(list(count_res.scalars().all()))
        return items, total
