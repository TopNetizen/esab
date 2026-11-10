"""各软件连接结果。live_verified 只有在本进程里握手成功时才为真。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

_SECRET_ENV = ("MIDAS_MAPI_KEY", "ESAB_TOKEN", "BIMBASE_MCP_URL", "HVAC_FORECAST_TOKEN")


def redact(text: str) -> str:
    cleaned = text
    for name in _SECRET_ENV:
        value = os.environ.get(name, "")
        if len(value) >= 4:
            cleaned = cleaned.replace(value, "***")
    return cleaned


@dataclass
class ConnectResult:
    ok: bool
    software: str
    message: str
    evidence: str
    entry: str
    live_verified: bool = False
    server_name: str | None = None
    injected: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.message = redact(self.message)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "software": self.software,
            "message": self.message,
            "evidence": self.evidence,
            "entry": self.entry,
            "live_verified": self.live_verified,
            "server_name": self.server_name,
            "injected": self.injected,
            "details": self.details,
        }
