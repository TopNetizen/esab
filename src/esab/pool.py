"""连接上游 MCP 服务，并按原样转发 tools / resources / prompts。"""

from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any

import mcp.types as types
from mcp import Client
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp_types import PaginatedRequestParams

from esab.catalog import BRIDGE_TOOL_PREFIX, UPSTREAM_NAME_SEPARATOR
from esab.config import ServerSpec, dump_public_specs

logger = logging.getLogger(__name__)

_EMPTY_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "additionalProperties": False}


@dataclass
class UpstreamLink:
    spec: ServerSpec
    adapter: "_Adapter | None"
    error: str | None


class _Adapter:
    def __init__(self, client: Client | None = None, session: ClientSession | None = None) -> None:
        self._client = client
        self._session = session

    async def list_tools(self, cursor: str | None) -> types.ListToolsResult:
        if self._client is not None:
            return await self._client.list_tools(cursor=cursor, cache_mode="refresh")
        assert self._session is not None
        return await self._session.list_tools(params=PaginatedRequestParams(cursor=cursor))

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        if self._client is not None:
            return await self._client.call_tool(name, arguments or {})
        assert self._session is not None
        return await self._session.call_tool(name, arguments or {})

    async def list_resources(self, cursor: str | None) -> types.ListResourcesResult:
        if self._client is not None:
            return await self._client.list_resources(cursor=cursor, cache_mode="refresh")
        assert self._session is not None
        return await self._session.list_resources(params=PaginatedRequestParams(cursor=cursor))

    async def read_resource(self, uri: str) -> types.ReadResourceResult:
        if self._client is not None:
            return await self._client.read_resource(uri, cache_mode="refresh")
        assert self._session is not None
        return await self._session.read_resource(uri)

    async def list_prompts(self, cursor: str | None) -> types.ListPromptsResult:
        if self._client is not None:
            return await self._client.list_prompts(cursor=cursor, cache_mode="refresh")
        assert self._session is not None
        return await self._session.list_prompts(params=PaginatedRequestParams(cursor=cursor))

    async def get_prompt(self, name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        if self._client is not None:
            return await self._client.get_prompt(name, arguments)
        assert self._session is not None
        return await self._session.get_prompt(name, arguments)


class UpstreamPool:
    def __init__(self, specs: list[ServerSpec]) -> None:
        self.specs = specs
        self.links: list[UpstreamLink] = []
        self._stack = AsyncExitStack()

    @property
    def enabled(self) -> list[ServerSpec]:
        return [spec for spec in self.specs if spec.enabled]

    @property
    def prefix_tools(self) -> bool:
        return len(self.enabled) > 1

    async def open(self) -> None:
        await self._stack.__aenter__()
        for spec in self.specs:
            if not spec.enabled:
                self.links.append(UpstreamLink(spec, None, None))
                continue
            try:
                adapter = await self._connect(spec)
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                logger.error("上游 %s 连接失败: %s", spec.id, message)
                self.links.append(UpstreamLink(spec, None, message))
            else:
                self.links.append(UpstreamLink(spec, adapter, None))

    async def close(self) -> None:
        await self._stack.aclose()

    async def _connect(self, spec: ServerSpec) -> _Adapter:
        if spec.transport == "stdio":
            if not spec.command:
                raise ValueError("stdio 上游缺少 command")
            params = StdioServerParameters(
                command=spec.command,
                args=list(spec.args),
                env=spec.env,
                cwd=spec.cwd,
            )
            client = Client(params, cache=None, mode="legacy")
            await self._stack.enter_async_context(client)
            return _Adapter(client=client)
        if not spec.url:
            raise ValueError("streamable_http 上游缺少 url")
        if spec.headers:
            http = create_mcp_http_client(headers=spec.headers)
            await self._stack.enter_async_context(http)
            read_stream, write_stream = await self._stack.enter_async_context(
                streamable_http_client(spec.url, http_client=http)
            )
            session = ClientSession(read_stream, write_stream)
            await self._stack.enter_async_context(session)
            await session.initialize()
            return _Adapter(session=session)
        client = Client(spec.url, cache=None, mode="legacy")
        await self._stack.enter_async_context(client)
        return _Adapter(client=client)

    def status(self) -> dict[str, Any]:
        rows = []
        public = {item["id"]: item for item in dump_public_specs(self.specs)}
        for link in self.links:
            row = dict(public[link.spec.id])
            row["connected"] = link.adapter is not None
            row["error"] = link.error
            rows.append(row)
        return {
            "bridge": "esab",
            "role": "proxy",
            "simulated_fixture_only": False,
            "tool_prefix_when_multiple_upstreams": self.prefix_tools,
            "bridge_tools_are_not_upstream_tools": True,
            "upstreams": rows,
        }

    def _public_name(self, spec: ServerSpec, name: str) -> str:
        if self.prefix_tools:
            return f"{spec.id}{UPSTREAM_NAME_SEPARATOR}{name}"
        return name

    def _resolve(self, public_name: str) -> tuple[UpstreamLink, str] | None:
        connected = [link for link in self.links if link.adapter is not None]
        if self.prefix_tools:
            for link in connected:
                prefix = f"{link.spec.id}{UPSTREAM_NAME_SEPARATOR}"
                if public_name.startswith(prefix):
                    return link, public_name[len(prefix) :]
            return None
        if len(connected) == 1:
            return connected[0], public_name
        return None

    async def list_tools(self, cursor: str | None) -> types.ListToolsResult:
        tools = self._bridge_tools() if not cursor else []
        next_cursor: str | None = None
        connected = [link for link in self.links if link.adapter is not None]
        if len(connected) == 1:
            link = connected[0]
            assert link.adapter is not None
            page = await link.adapter.list_tools(cursor)
            tools.extend(page.tools)
            next_cursor = page.next_cursor
        elif not cursor:
            for link in connected:
                assert link.adapter is not None
                page = await link.adapter.list_tools(None)
                for tool in page.tools:
                    tools.append(tool.model_copy(update={"name": self._public_name(link.spec, tool.name)}))
                if page.next_cursor:
                    logger.warning("上游 %s 的工具列表还有后续页，多上游模式只转发第一页", link.spec.id)
        return types.ListToolsResult(tools=tools, next_cursor=next_cursor)

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> types.CallToolResult:
        if name == "esab_status":
            return _json_result(self.status())
        if name == "esab_list_servers":
            return _json_result({"servers": self.status()["upstreams"]})
        if name.startswith(BRIDGE_TOOL_PREFIX):
            return _error_result(f"未知的桥接器工具: {name}")
        resolved = self._resolve(name)
        if resolved is None:
            failed = [link for link in self.links if link.spec.enabled and link.error]
            if failed and not self.prefix_tools:
                return _error_result(failed[0].error or "上游未连接")
            return _error_result(f"没有名为 {name} 的上游工具。桥接器不会编造上游工具。")
        link, upstream_name = resolved
        assert link.adapter is not None
        try:
            return await link.adapter.call_tool(upstream_name, arguments)
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            logger.exception("调用上游 %s 工具 %s 失败", link.spec.id, upstream_name)
            return _error_result(message)

    async def list_resources(self, cursor: str | None) -> types.ListResourcesResult:
        connected = [link for link in self.links if link.adapter is not None]
        if len(connected) != 1:
            return types.ListResourcesResult(resources=[])
        page = await connected[0].adapter.list_resources(cursor)  # type: ignore[union-attr]
        return page

    async def read_resource(self, uri: str) -> types.ReadResourceResult:
        connected = [link for link in self.links if link.adapter is not None]
        if len(connected) != 1:
            raise ValueError("当前没有唯一已连接的上游，无法按原 URI 读取资源")
        return await connected[0].adapter.read_resource(uri)  # type: ignore[union-attr]

    async def list_prompts(self, cursor: str | None) -> types.ListPromptsResult:
        connected = [link for link in self.links if link.adapter is not None]
        if len(connected) != 1:
            return types.ListPromptsResult(prompts=[])
        return await connected[0].adapter.list_prompts(cursor)  # type: ignore[union-attr]

    async def get_prompt(self, name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
        connected = [link for link in self.links if link.adapter is not None]
        if len(connected) != 1:
            raise ValueError("当前没有唯一已连接的上游，无法按原名读取 prompt")
        return await connected[0].adapter.get_prompt(name, arguments)  # type: ignore[union-attr]

    def _bridge_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="esab_status",
                title="桥接器状态",
                description="报告桥接器与上游的连接状态。这是桥接器自己的诊断工具，不是上游软件工具。",
                input_schema=_EMPTY_SCHEMA,
            ),
            types.Tool(
                name="esab_list_servers",
                title="上游服务列表",
                description="列出配置中的上游服务及连接错误。这是桥接器自己的诊断工具，不是上游软件工具。",
                input_schema=_EMPTY_SCHEMA,
            ),
        ]


def _json_result(payload: dict[str, Any]) -> types.CallToolResult:
    text = __import__("json").dumps(payload, ensure_ascii=False)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=text)],
        structured_content=payload,
        is_error=False,
    )


def _error_result(message: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=message)], is_error=True)
