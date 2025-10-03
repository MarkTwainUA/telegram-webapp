from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class JSONRPCRequest(BaseModel):
    jsonrpc: str
    id: str
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
