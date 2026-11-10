"""对外的标准 MCP 服务。工具语义来自上游，不在这里重写。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import mcp.types as types
from mcp.server import Server

from esab import __version__
from esab.config import ServerSpec
from esab.pool import UpstreamPool

INSTRUCTIONS = (
    "这是工程软件 MCP 的桥接器，不是结构设计程序。"
    "esab_ 开头的工具只报告桥接状态。"
    "其余工具、资源和 prompt 原样来自已连接的上游；上游没连上时不会出现虚构的建模或计算工具。"
    "工程计算结果和规范符合性必须由有资质的工程师核对。"
    "模拟夹具会在工具说明里标明 SIMULATED，不能当成真实工程软件。"
)


def build_server(specs: list[ServerSpec]) -> Server[UpstreamPool]:
    pool_box: dict[str, UpstreamPool] = {}

    @asynccontextmanager
    async def lifespan(_server: Server[UpstreamPool]) -> AsyncIterator[UpstreamPool]:
        pool = UpstreamPool(specs)
        await pool.open()
        pool_box["pool"] = pool
        try:
            yield pool
        finally:
            await pool.close()

    def pool_from(ctx: object) -> UpstreamPool:
        lifespan_context = getattr(ctx, "lifespan_context", None)
        if isinstance(lifespan_context, UpstreamPool):
            return lifespan_context
        if "pool" in pool_box:
            return pool_box["pool"]
        raise RuntimeError("桥接器尚未连接上游")

    async def on_list_tools(ctx: object, params: types.PaginatedRequestParams | None) -> types.ListToolsResult:
        cursor = params.cursor if params is not None else None
        return await pool_from(ctx).list_tools(cursor)

    async def on_call_tool(ctx: object, params: types.CallToolRequestParams) -> types.CallToolResult:
        arguments = params.arguments if isinstance(params.arguments, dict) else None
        return await pool_from(ctx).call_tool(params.name, arguments)

    async def on_list_resources(
        ctx: object, params: types.PaginatedRequestParams | None
    ) -> types.ListResourcesResult:
        cursor = params.cursor if params is not None else None
        return await pool_from(ctx).list_resources(cursor)

    async def on_read_resource(ctx: object, params: types.ReadResourceRequestParams) -> types.ReadResourceResult:
        return await pool_from(ctx).read_resource(str(params.uri))

    async def on_list_prompts(ctx: object, params: types.PaginatedRequestParams | None) -> types.ListPromptsResult:
        cursor = params.cursor if params is not None else None
        return await pool_from(ctx).list_prompts(cursor)

    async def on_get_prompt(ctx: object, params: types.GetPromptRequestParams) -> types.GetPromptResult:
        return await pool_from(ctx).get_prompt(params.name, params.arguments)

    return Server(
        "esab",
        version=__version__,
        title="Engineering Software Agent Bridge",
        instructions=INSTRUCTIONS,
        lifespan=lifespan,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
        on_list_resources=on_list_resources,
        on_read_resource=on_read_resource,
        on_list_prompts=on_list_prompts,
        on_get_prompt=on_get_prompt,
    )
