from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx
import pytest
from httpx import Response
from httpx._transports.mock import MockTransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_sessionmaker, init_db
from app.tools.schemas import CreatePostInput, UpdatePostInput
from app.tools.telegram_client import TelegramClient
from app.tools.telegram_tools import create_post, delete_post, get_post, list_posts, update_post


@pytest.fixture(scope="module")
async def db_setup():
    await init_db()


def make_telegram_transport():
    def handler(request: httpx.Request) -> Response:
        url = str(request.url)
        data = json.loads(request.content.decode() or "{}")
        if url.endswith("sendMessage"):
            result = {
                "message_id": 42,
                "date": 1700000000,
                "text": data.get("text"),
                "chat": {"id": -100123, "username": "mychan"},
            }
            return Response(200, json={"ok": True, "result": result})
        if url.endswith("editMessageText") or url.endswith("editMessageCaption"):
            result = {
                "message": {
                    "message_id": data.get("message_id"),
                    "date": 1700000100,
                    "text": data.get("text"),
                    "caption": data.get("caption"),
                    "chat": {"id": -100123, "username": "mychan"},
                }
            }
            return Response(200, json={"ok": True, "result": result})
        if url.endswith("deleteMessage"):
            return Response(200, json={"ok": True, "result": True})
        raise RuntimeError("Unexpected URL")

    return MockTransport(handler)


@pytest.mark.asyncio
async def test_create_update_delete_list_get(db_setup):
    session_maker = get_sessionmaker()

    transport = make_telegram_transport()
    async with httpx.AsyncClient(transport=transport) as client:
        tg = TelegramClient(client=client)
        async with session_maker() as session:  # type: AsyncSession
            # create
            create_args = CreatePostInput(chat_id="@mychan", text="Hello", parse_mode="HTML")
            created = await create_post(session, tg, create_args, idempotency_key="key1")
            await session.commit()
            assert created.message_id == 42
            assert created.link == "https://t.me/mychan/42"

            # update
            update_args = UpdatePostInput(chat_id="@mychan", message_id=42, text="Updated", parse_mode="HTML")
            updated = await update_post(session, tg, update_args)
            await session.commit()
            assert updated.edited is True

            # get
            got = await get_post(session, create_args.model_copy(update={"message_id": 42}))
            assert got.message_id == 42
            assert got.text in ("Hello", "Updated")

            # list
            listed = await list_posts(session, create_args.model_copy(update={"limit": 10, "offset": 0}))
            assert listed.total >= 1

            # delete
            deleted = await delete_post(session, tg, create_args.model_copy(update={"message_id": 42}))
            await session.commit()
            assert deleted.deleted is True

        await tg.aclose()
