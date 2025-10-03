from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    TELEGRAM_BOT_TOKEN: str = "TEST:TOKEN"
    ALLOWED_CHAT_IDS: str = "*"  # comma-separated list of allowed chat ids or "*"
    API_KEY: str = "change-me"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"
    BASE_URL: str = "http://localhost:8000"
    RATE_LIMIT: str = "10/second"  # e.g., "10/second" or "100/minute"

    def allowed_chat_ids(self) -> List[str]:
        value = (self.ALLOWED_CHAT_IDS or "").strip()
        if value == "*" or value == "":
            return ["*"]
        return [v.strip() for v in value.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
