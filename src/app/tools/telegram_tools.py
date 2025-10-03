from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from ..repository import PostRepository
from ..security import ensure_chat_allowed
from .schemas import (
    CreatePostInput,
    CreatePostOutput,
    DeletePostInput,
    DeletePostOutput,
    GetPostInput,
    GetPostOutput,
    ListPostsInput,
    ListPostsOutput,
    UpdatePostInput,
    UpdatePostOutput,
)
from .telegram_client import TelegramClient


def _extract_message_fields(data: dict[str, Any]) -> dict[str, Any]:
    result = data.get("result") or {}
    message = result if result.get("message_id") else result.get("message", {})
    chat = message.get("chat", {})
    message_id = message.get("message_id")
    date = message.get("date")
    text = message.get("text")
    caption = message.get("caption")
    link = None
    username = chat.get("username")
    if username and message_id:
        link = f"https://t.me/{username}/{message_id}"
    chat_id = chat.get("id")
    return {
        "message_id": int(message_id) if message_id is not None else None,
        "chat_id": int(chat_id) if chat_id is not None else None,
        "date": int(date) if date is not None else None,
        "text": text,
        "caption": caption,
        "username": username,
        "link": link,
    }


async def create_post(session: AsyncSession, client: TelegramClient, args: CreatePostInput, *, idempotency_key: str | None) -> CreatePostOutput:
    ensure_chat_allowed(args.chat_id)
    data = await client.send_message(
        chat_id=args.chat_id,
        text=args.text,
        caption=args.caption,
        parse_mode=args.parse_mode,
        disable_web_page_preview=args.disable_web_page_preview,
        reply_markup=args.reply_markup,
    )
    fields = _extract_message_fields(data)
    repo = PostRepository(session)
    post = await repo.upsert_post(
        chat_id=str(args.chat_id),
        message_id=fields["message_id"],
        text=fields.get("text"),
        caption=fields.get("caption"),
        parse_mode=args.parse_mode,
        disable_preview=args.disable_web_page_preview,
        date=fields["date"],
        username=fields.get("username"),
        link=fields.get("link"),
        idempotency_key=idempotency_key,
    )
    return CreatePostOutput(
        message_id=post.message_id,
        chat_id=int(post.chat_id) if str(post.chat_id).lstrip("-+").isdigit() else fields["chat_id"],
        link=post.link,
        date=post.date,
        text=post.text,
        caption=post.caption,
    )


async def update_post(session: AsyncSession, client: TelegramClient, args: UpdatePostInput) -> UpdatePostOutput:
    ensure_chat_allowed(args.chat_id)
    data = await client.edit_message(
        chat_id=args.chat_id,
        message_id=args.message_id,
        text=args.text,
        caption=args.caption,
        parse_mode=args.parse_mode,
        disable_web_page_preview=args.disable_web_page_preview,
    )
    fields = _extract_message_fields(data)
    repo = PostRepository(session)
    post = await repo.upsert_post(
        chat_id=str(args.chat_id),
        message_id=args.message_id,
        text=fields.get("text") or args.text,
        caption=fields.get("caption") or args.caption,
        parse_mode=args.parse_mode,
        disable_preview=args.disable_web_page_preview,
        date=fields["date"],
        username=fields.get("username"),
        link=fields.get("link"),
    )
    return UpdatePostOutput(
        message_id=post.message_id,
        chat_id=int(post.chat_id) if str(post.chat_id).lstrip("-+").isdigit() else fields["chat_id"],
        edited=True,
        date=post.date,
    )


async def delete_post(session: AsyncSession, client: TelegramClient, args: DeletePostInput) -> DeletePostOutput:
    ensure_chat_allowed(args.chat_id)
    await client.delete_message(chat_id=args.chat_id, message_id=args.message_id)
    repo = PostRepository(session)
    await repo.delete_by_chat_and_message(str(args.chat_id), args.message_id)
    return DeletePostOutput(deleted=True)


async def get_post(session: AsyncSession, args: GetPostInput) -> GetPostOutput:
    ensure_chat_allowed(args.chat_id)
    repo = PostRepository(session)
    post = await repo.get_by_chat_and_message(str(args.chat_id), args.message_id)
    if not post:
        raise ValueError("Post not found")
    return GetPostOutput(
        message_id=post.message_id,
        chat_id=int(post.chat_id) if str(post.chat_id).lstrip("-+").isdigit() else 0,
        date=post.date,
        text=post.text,
        caption=post.caption,
        link=post.link,
    )


async def list_posts(session: AsyncSession, args: ListPostsInput) -> ListPostsOutput:
    ensure_chat_allowed(args.chat_id)
    repo = PostRepository(session)
    items, total = await repo.list_posts(str(args.chat_id), args.limit, args.offset)
    return ListPostsOutput(
        items=[
            GetPostOutput(
                message_id=i.message_id,
                chat_id=int(i.chat_id) if str(i.chat_id).lstrip("-+").isdigit() else 0,
                date=i.date,
                text=i.text,
                caption=i.caption,
                link=i.link,
            )
            for i in items
        ],
        total=total,
        limit=args.limit,
        offset=args.offset,
    )
