"""连接用户本机已经发布的 MCP。不启动未授权的软件进程。"""

from __future__ import annotations

import asyncio
import os
import threading
from typing import Any

from mcp import Client

from esab.adapters.common import ConnectResult
from esab.runtime.state import STATE, BoundTool

_LOOP = asyncio.new_event_loop()
_THREAD = threading.Thread(target=_LOOP.run_forever, name="struct-mcp-upstream", daemon=True)
_THREAD.start()
_CLIENTS: dict[str, Client] = {}


def _run(coro: Any) -> Any:
    future = asyncio.run_coroutine_threadsafe(coro, _LOOP)
    return future.result()


async def _open(url: str) -> tuple[Client, list[Any], int]:
    client = Client(url, cache=None, mode="legacy")
    await client.__aenter__()
    tools: list[Any] = []
    cursor = None
    pages = 0
    while pages < 20:
        page = await client.list_tools(cursor=cursor, cache_mode="refresh")
        tools.extend(page.tools)
        pages += 1
        cursor = page.next_cursor
        if not cursor:
            break
    return client, tools, pages


def connect_streamable(server_name: str, url: str, software: str, evidence: str) -> ConnectResult:
    if not url:
        return ConnectResult(
            ok=False,
            software=software,
            server_name=server_name,
            message=f"没有 {software} 的 MCP 地址。请先打开已授权软件，再用环境变量或诊断脚本提供 URL。",
            evidence=evidence,
            entry="adapters.mcp_upstream.connect_streamable",
        )
    try:
        client, tools, pages = _run(_open(url))
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software=software,
            server_name=server_name,
            message=f"连接 {url} 失败：{type(exc).__name__}: {exc}",
            evidence=evidence,
            entry="adapters.mcp_upstream.connect_streamable",
            details={"url": url},
        )
    _CLIENTS[server_name] = client
    injected: list[str] = []
    namespace: dict[str, Any] = {}

    def _make_call(tool_name: str, active: Client):
        def _call(**arguments: Any) -> Any:
            result = _run(active.call_tool(tool_name, arguments))
            if getattr(result, "structured_content", None) is not None:
                return result.structured_content
            texts = [getattr(block, "text", str(block)) for block in (result.content or [])]
            if getattr(result, "is_error", False):
                raise RuntimeError("\n".join(texts))
            return "\n".join(texts)

        return _call

    for tool in tools:
        category = f"{server_name}{tool.title}" if getattr(tool, "title", None) else server_name
        bound = BoundTool(
            server_name=server_name,
            name=tool.name,
            description=tool.description or "",
            input_schema=dict(tool.input_schema or {}),
            category=category,
            call=_make_call(tool.name, client),
        )
        STATE.tools[f"{server_name}.{tool.name}"] = bound
        namespace[tool.name] = bound.call
        injected.append(tool.name)
    STATE.connections[server_name] = {"url": url, "software": software, "ok": True}
    return ConnectResult(
        ok=True,
        software=software,
        server_name=server_name,
        message=f"已连接 {software}，注入 {len(injected)} 个上游工具。",
        evidence=evidence,
        entry="adapters.mcp_upstream.connect_streamable",
        live_verified=True,
        injected=injected,
        details={"url": url, "pages": pages, "namespace": namespace},
    )


def disconnect(server_name: str) -> None:
    client = _CLIENTS.pop(server_name, None)
    if client is not None:
        try:
            _run(client.__aexit__(None, None, None))
        except Exception:
            pass
    STATE.connections.pop(server_name, None)
    for key in [key for key, tool in STATE.tools.items() if tool.server_name == server_name]:
        STATE.tools.pop(key, None)


def url_from_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""
