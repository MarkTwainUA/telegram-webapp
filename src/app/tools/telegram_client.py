from __future__ import annotations

import random
from typing import Any, Dict, Optional

import httpx
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from ..config import get_settings


class TelegramAPIError(Exception):
    def __init__(self, message: str, *, code: int | None = None, data: dict | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data or {}


class TelegramClient:
    def __init__(self, client: Optional[httpx.AsyncClient] = None) -> None:
        self.settings = get_settings()
        self.base_url = f"https://api.telegram.org/bot{self.settings.TELEGRAM_BOT_TOKEN}"
        self.client = client or httpx.AsyncClient(timeout=httpx.Timeout(10.0, read=20.0))

    async def aclose(self) -> None:
        await self.client.aclose()

    def _link_from(self, chat: dict[str, Any], message_id: int) -> tuple[Optional[str], Optional[str]]:
        username = chat.get("username")
        link: Optional[str] = None
        if username:
            link = f"https://t.me/{username}/{message_id}"
        return link, username

    def _raise_for_response(self, data: dict[str, Any]) -> None:
        if not data.get("ok"):
            description = data.get("description", "Telegram API error")
            error_code = data.get("error_code")
            raise TelegramAPIError(description, code=error_code, data=data)

    @retry(
        reraise=True,
        retry=retry_if_exception_type((httpx.HTTPError, TelegramAPIError)),
        wait=wait_exponential_jitter(initial=0.5, max=5.0),
        stop=stop_after_attempt(5),
    )
    async def _post(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}"
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        self._raise_for_response(data)
        return data

    async def send_message(
        self,
        *,
        chat_id: str | int,
        text: str | None,
        caption: str | None,
        parse_mode: str | None,
        disable_web_page_preview: bool | None,
        reply_markup: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id}
        if text:
            payload["text"] = text
        if caption:
            payload["caption"] = caption
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if disable_web_page_preview is not None:
            payload["disable_web_page_preview"] = disable_web_page_preview
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        # Bot API: for text posts, use sendMessage; captions are ignored there.
        if text is None and caption is not None:
            # Use sendMessage with caption? Not supported; for channels, captions apply to media. We treat caption as text for now.
            payload["text"] = caption
            payload.pop("caption", None)
        data = await self._post("sendMessage", payload)
        return data

    async def edit_message(
        self,
        *,
        chat_id: str | int,
        message_id: int,
        text: str | None,
        caption: str | None,
        parse_mode: str | None,
        disable_web_page_preview: bool | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "message_id": message_id}
        if text is not None:
            payload["text"] = text
            if parse_mode:
                payload["parse_mode"] = parse_mode
            if disable_web_page_preview is not None:
                payload["disable_web_page_preview"] = disable_web_page_preview
            method = "editMessageText"
        elif caption is not None:
            payload["caption"] = caption
            if parse_mode:
                payload["parse_mode"] = parse_mode
            method = "editMessageCaption"
        else:
            raise TelegramAPIError("Either text or caption must be provided for edit")
        data = await self._post(method, payload)
        return data

    async def delete_message(self, *, chat_id: str | int, message_id: int) -> dict[str, Any]:
        payload = {"chat_id": chat_id, "message_id": message_id}
        data = await self._post("deleteMessage", payload)
        return data
