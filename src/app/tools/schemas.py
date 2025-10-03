from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


ParseMode = Literal["MarkdownV2", "HTML"]


class CreatePostInput(BaseModel):
    chat_id: str | int
    text: Optional[str] = None
    caption: Optional[str] = None
    parse_mode: Optional[ParseMode] = None
    disable_web_page_preview: Optional[bool] = None
    reply_markup: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def check_content(self):  # type: ignore[override]
        if not self.text and not self.caption:
            raise ValueError("Either text or caption must be provided")
        return self


class CreatePostOutput(BaseModel):
    message_id: int
    chat_id: int
    link: Optional[str] = None
    date: int
    text: Optional[str] = None
    caption: Optional[str] = None


class UpdatePostInput(BaseModel):
    chat_id: str | int
    message_id: int
    text: Optional[str] = None
    caption: Optional[str] = None
    parse_mode: Optional[ParseMode] = None
    disable_web_page_preview: Optional[bool] = None

    @model_validator(mode="after")
    def check_one(self):  # type: ignore[override]
        if not self.text and not self.caption:
            raise ValueError("Either text or caption must be provided for update")
        return self


class UpdatePostOutput(BaseModel):
    message_id: int
    chat_id: int
    edited: bool
    date: int


class DeletePostInput(BaseModel):
    chat_id: str | int
    message_id: int


class DeletePostOutput(BaseModel):
    deleted: bool


class GetPostInput(BaseModel):
    chat_id: str | int
    message_id: int


class GetPostOutput(BaseModel):
    message_id: int
    chat_id: int
    date: int
    text: Optional[str] = None
    caption: Optional[str] = None
    link: Optional[str] = None


class ListPostsInput(BaseModel):
    chat_id: str | int
    limit: int = Field(default=20, le=100)
    offset: int = 0


class ListPostsOutput(BaseModel):
    items: list[GetPostOutput]
    total: int
    limit: int
    offset: int
