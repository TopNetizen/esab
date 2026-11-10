"""标准 MCP 入口。客户端负责推理，这里提供技能、持久 Python 和连接。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import mcp.types as types
from mcp.server import Server

from esab import __version__
from esab.adapters.hosts import CATALOG
from esab.runtime.skills_api import find_skill, iter_skill_files, skill_name
from esab.runtime.worker import WorkerPool

INSTRUCTIONS = (
    "这是桥接器技能所使用的执行入口，独立 MCP 服务。"
    "先用 resources 读取原始 SKILL.md，再在 python_executor 中调用 connect_to_server、"
    "function_search 和 use_skill。这些函数已经注入执行环境。"
    "软件必须由用户事先打开并完成授权。连接失败时返回诊断，不表示操作已成功。"
    "本工具不判断结构是否符合规范。"
)


def build_agent_server() -> Server[WorkerPool]:
    pool = WorkerPool()

    @asynccontextmanager
    async def lifespan(_server: Server[WorkerPool]) -> AsyncIterator[WorkerPool]:
        yield pool

    async def on_list_tools(_ctx: object, _params: types.PaginatedRequestParams | None) -> types.ListToolsResult:
        return types.ListToolsResult(
            tools=[
                types.Tool(
                    name="python_executor",
                    description="在会话持久的 Python 环境中执行代码。connect_to_server、function_search、use_skill 已注入。",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "session_id": {"type": "string"},
                            "timeout_seconds": {"type": "number"},
                        },
                        "required": ["code"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="use_skill",
                    description="按原始文件读取技能，或运行技能目录里的脚本。不修改技能正文。",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "file": {"type": "string"},
                            "run": {"type": "string"},
                            "run_args": {"type": "string"},
                        },
                        "required": ["name"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="cancel_execution",
                    description="终止该会话正在执行的 Python，并重建进程。未完成的软件调用会中断。",
                    input_schema={
                        "type": "object",
                        "properties": {"session_id": {"type": "string"}},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="list_software_adapters",
                    description="列出 15 类软件的连接入口、证据和当前是否已做实机验证。",
                    input_schema={"type": "object", "properties": {}, "additionalProperties": False},
                ),
            ]
        )

    async def on_call_tool(_ctx: object, params: types.CallToolRequestParams) -> types.CallToolResult:
        arguments = params.arguments if isinstance(params.arguments, dict) else {}
        if params.name == "list_software_adapters":
            return _text(json_dumps({"adapters": CATALOG, "live_software_calls_in_linux_tests": 0}))
        if params.name == "cancel_execution":
            session_id = str(arguments.get("session_id") or "default")
            pool.get(session_id).cancel()
            return _text(
                json_dumps(
                    {
                        "session_id": session_id,
                        "worker_terminated": True,
                        "software_operation_cancelled": False,
                        "message": "只结束了本会话的 Python 进程。已经提交给目标软件的计算不会因此停止。",
                    }
                )
            )
        if params.name == "use_skill":
            code = (
                "print(use_skill("
                f"{arguments.get('name')!r}, file={arguments.get('file')!r}, "
                f"run={arguments.get('run')!r}, run_args={arguments.get('run_args') or ''!r}))"
            )
            result = pool.get(str(arguments.get("session_id") or "default")).execute(code, timeout=120)
            return _from_exec(result)
        if params.name == "python_executor":
            session_id = str(arguments.get("session_id") or "default")
            timeout = arguments.get("timeout_seconds")
            timeout_value = float(timeout) if isinstance(timeout, (int, float)) else None
            result = pool.get(session_id).execute(str(arguments.get("code") or ""), timeout_value)
            return _from_exec(result)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"未知工具 {params.name}")],
            is_error=True,
        )

    async def on_list_resources(_ctx: object, _params: types.PaginatedRequestParams | None) -> types.ListResourcesResult:
        resources = [
            types.Resource(
                name=skill_name(path),
                uri=f"skill://{skill_name(path)}/SKILL.md",
                description="本技能正文",
                mime_type="text/markdown",
            )
            for path in iter_skill_files() or []
        ]
        return types.ListResourcesResult(resources=resources)

    async def on_read_resource(_ctx: object, params: types.ReadResourceRequestParams) -> types.ReadResourceResult:
        uri = str(params.uri)
        name = uri.removeprefix("skill://").split("/", 1)[0]
        path = find_skill(name)
        if path is None:
            raise ValueError(f"没有技能资源 {uri}。设置 ESAB_SKILLS_ROOT 后重试。")
        return types.ReadResourceResult(
            contents=[types.TextResourceContents(uri=uri, mime_type="text/markdown", text=path.read_text(encoding="utf-8"))]
        )

    return Server(
        "esab-runtime",
        version=__version__,
        title="ESAB engineering software runtime",
        instructions=INSTRUCTIONS,
        lifespan=lifespan,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
        on_list_resources=on_list_resources,
        on_read_resource=on_read_resource,
    )


def _text(text: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=False)


def _from_exec(result: dict[str, str | bool]) -> types.CallToolResult:
    stdout = str(result.get("stdout") or "")
    error = str(result.get("error") or "")
    body = stdout if result.get("ok") else stdout + error
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=body)],
        is_error=not bool(result.get("ok")),
    )


def json_dumps(payload: object) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)
