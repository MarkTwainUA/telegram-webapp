from __future__ import annotations

import json
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST

from .db import get_sessionmaker
from .sse import sse_manager
from .tools.schemas import (
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
from .tools.telegram_client import TelegramAPIError, TelegramClient
from .tools.telegram_tools import create_post, delete_post, get_post, list_posts, update_post


TOOLS_SPEC = [
    {
        "name": "telegram.create_post",
        "description": "Create a post in a Telegram channel",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "chat_id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                "text": {"type": "string"},
                "caption": {"type": "string"},
                "parse_mode": {"type": "string", "enum": ["MarkdownV2", "HTML"]},
                "disable_web_page_preview": {"type": "boolean"},
                "reply_markup": {"type": "object"},
            },
            "required": ["chat_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"},
                "chat_id": {"type": "integer"},
                "link": {"type": ["string", "null"]},
                "date": {"type": "integer"},
                "text": {"type": ["string", "null"]},
                "caption": {"type": ["string", "null"]},
            },
            "required": ["message_id", "chat_id", "date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "telegram.update_post",
        "description": "Update a Telegram channel post",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "chat_id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                "message_id": {"type": "integer"},
                "text": {"type": "string"},
                "caption": {"type": "string"},
                "parse_mode": {"type": "string", "enum": ["MarkdownV2", "HTML"]},
                "disable_web_page_preview": {"type": "boolean"},
            },
            "required": ["chat_id", "message_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"},
                "chat_id": {"type": "integer"},
                "edited": {"type": "boolean"},
                "date": {"type": "integer"},
            },
            "required": ["message_id", "chat_id", "edited", "date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "telegram.delete_post",
        "description": "Delete a Telegram channel post",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "chat_id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                "message_id": {"type": "integer"},
            },
            "required": ["chat_id", "message_id"],
            "additionalProperties": False,
        },
        "outputSchema": {"type": "object", "properties": {"deleted": {"type": "boolean"}}, "required": ["deleted"], "additionalProperties": False},
    },
    {
        "name": "telegram.get_post",
        "description": "Fetch a Telegram post from DB",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "chat_id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                "message_id": {"type": "integer"},
            },
            "required": ["chat_id", "message_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "integer"},
                "chat_id": {"type": "integer"},
                "date": {"type": "integer"},
                "text": {"type": ["string", "null"]},
                "caption": {"type": ["string", "null"]},
                "link": {"type": ["string", "null"]},
            },
            "required": ["message_id", "chat_id", "date"],
            "additionalProperties": False,
        },
    },
    {
        "name": "telegram.list_posts",
        "description": "List Telegram posts from DB",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "chat_id": {"oneOf": [{"type": "string"}, {"type": "integer"}]},
                "limit": {"type": "integer", "maximum": 100, "default": 20},
                "offset": {"type": "integer", "default": 0},
            },
            "required": ["chat_id"],
            "additionalProperties": False,
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "items": {"type": "array"},
                "total": {"type": "integer"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"},
            },
            "required": ["items", "total", "limit", "offset"],
            "additionalProperties": False,
        },
    },
]


def jsonrpc_result(request_id: str, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def jsonrpc_error(request_id: str, code: int, message: str, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message, "data": data or {}}}


async def handle_tools_list(request_id: str) -> dict[str, Any]:
    return jsonrpc_result(request_id, {"tools": TOOLS_SPEC})


async def handle_tools_call(request: Request, request_id: str, params: dict[str, Any]) -> dict[str, Any]:
    name: str = params.get("name")
    arguments: dict[str, Any] = params.get("arguments") or {}
    idempotency_key: Optional[str] = params.get("idempotency_key")
    if not name:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing tool name")

    session_maker = get_sessionmaker()
    async with session_maker() as session:
        client = TelegramClient()
        try:
            if name == "telegram.create_post":
                args = CreatePostInput(**arguments)
                output = await create_post(session, client, args, idempotency_key=idempotency_key)
                await session.commit()
                return jsonrpc_result(request_id, output.model_dump())
            elif name == "telegram.update_post":
                args = UpdatePostInput(**arguments)
                output = await update_post(session, client, args)
                await session.commit()
                return jsonrpc_result(request_id, output.model_dump())
            elif name == "telegram.delete_post":
                args = DeletePostInput(**arguments)
                output = await delete_post(session, client, args)
                await session.commit()
                return jsonrpc_result(request_id, output.model_dump())
            elif name == "telegram.get_post":
                args = GetPostInput(**arguments)
                output = await get_post(session, args)
                return jsonrpc_result(request_id, output.model_dump())
            elif name == "telegram.list_posts":
                args = ListPostsInput(**arguments)
                output = await list_posts(session, args)
                return jsonrpc_result(request_id, output.model_dump())
            else:
                return jsonrpc_error(request_id, -32601, f"Unknown tool: {name}")
        except TelegramAPIError as e:
            await session.rollback()
            return jsonrpc_error(request_id, -32000, str(e), data=e.data)
        except Exception as e:  # noqa: BLE001
            await session.rollback()
            return jsonrpc_error(request_id, -32000, str(e))
        finally:
            await client.aclose()


async def dispatch_jsonrpc(request: Request, payload: Dict[str, Any]) -> dict[str, Any]:
    if payload.get("jsonrpc") != "2.0":
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid JSON-RPC version")
    request_id = str(payload.get("id"))
    method = payload.get("method")
    params = payload.get("params") or {}

    if method == "tools/list":
        return await handle_tools_list(request_id)
    if method == "tools/call":
        result = await handle_tools_call(request, request_id, params)
        return result
    return jsonrpc_error(request_id, -32601, f"Unknown method: {method}")
