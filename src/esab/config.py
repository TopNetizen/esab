"""读取桥接配置。未知字段保留在 notes 之外并忽略，避免把注释当成协议。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from esab.catalog import SUPPORTED_UPSTREAM_TRANSPORTS


@dataclass(frozen=True)
class ServerSpec:
    id: str
    enabled: bool
    transport: str
    command: str | None = None
    args: tuple[str, ...] = ()
    env: dict[str, str] | None = None
    cwd: str | None = None
    url: str | None = None
    headers: dict[str, str] | None = None
    simulated: bool = False
    notes: str | None = None


def load_config(path: str | Path) -> list[ServerSpec]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("servers"), list):
        raise ValueError("配置必须是对象，且含 servers 数组")
    specs: list[ServerSpec] = []
    seen: set[str] = set()
    for item in raw["servers"]:
        if not isinstance(item, dict):
            raise ValueError("servers 中的每一项都必须是对象")
        server_id = str(item.get("id") or "").strip()
        if not server_id or any(ch.isspace() for ch in server_id):
            raise ValueError(f"非法的上游 id: {server_id!r}")
        if server_id in seen:
            raise ValueError(f"重复的上游 id: {server_id}")
        seen.add(server_id)
        transport = str(item.get("transport") or "").strip()
        if transport not in SUPPORTED_UPSTREAM_TRANSPORTS:
            raise ValueError(
                f"{server_id} 的 transport={transport!r} 不受桥接器支持。"
                f"可用值: {', '.join(SUPPORTED_UPSTREAM_TRANSPORTS)}"
            )
        args = item.get("args") or []
        if not isinstance(args, list) or not all(isinstance(part, str) for part in args):
            raise ValueError(f"{server_id} 的 args 必须是字符串数组")
        env = item.get("env")
        if env is not None and not isinstance(env, dict):
            raise ValueError(f"{server_id} 的 env 必须是对象")
        headers = item.get("headers")
        if headers is not None and not isinstance(headers, dict):
            raise ValueError(f"{server_id} 的 headers 必须是对象")
        specs.append(
            ServerSpec(
                id=server_id,
                enabled=bool(item.get("enabled", True)),
                transport=transport,
                command=item.get("command"),
                args=tuple(args),
                env={str(k): str(v) for k, v in env.items()} if env else None,
                cwd=item.get("cwd"),
                url=item.get("url"),
                headers={str(k): str(v) for k, v in headers.items()} if headers else None,
                simulated=bool(item.get("simulated", False)),
                notes=item.get("notes"),
            )
        )
    return specs


def dump_public_specs(specs: list[ServerSpec]) -> list[dict[str, Any]]:
    """给状态工具用。去掉请求头，避免把上游凭据写进对话。"""
    rows: list[dict[str, Any]] = []
    for spec in specs:
        rows.append(
            {
                "id": spec.id,
                "enabled": spec.enabled,
                "transport": spec.transport,
                "url": spec.url,
                "command": spec.command,
                "args": list(spec.args),
                "simulated": spec.simulated,
                "has_headers": bool(spec.headers),
                "notes": spec.notes,
            }
        )
    return rows
