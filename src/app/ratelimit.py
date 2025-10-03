from __future__ import annotations

from typing import Callable

from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)


def key_func_with_api_key(request) -> str:
    api_key = request.headers.get("X-API-Key", "")
    ip = get_remote_address(request)
    return f"{api_key}:{ip}"
