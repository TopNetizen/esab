"""模拟上游。只用于传输测试，不代表任何真实工程软件。"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

SIMULATED = "SIMULATED fixture. Not a real software tool and not a structural calculation."


def build_fixture_server() -> Server[None]:
    echo = types.Tool(
        name="fixture_echo",
        title="模拟回声",
        description=SIMULATED,
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
            "additionalProperties": False,
        },
    )
    fail = types.Tool(
        name="fixture_fail",
        title="模拟失败",
        description="SIMULATED fixture that returns an upstream tool error. Not a real software tool.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
    )

    async def on_list_tools(_ctx: object, params: types.PaginatedRequestParams | None) -> types.ListToolsResult:
        cursor = params.cursor if params is not None else None
        if os.environ.get("FIXTURE_PAGINATE") == "1":
            if cursor == "2":
                return types.ListToolsResult(tools=[fail])
            return types.ListToolsResult(tools=[echo], next_cursor="2")
        return types.ListToolsResult(tools=[echo, fail])

    async def on_call_tool(_ctx: object, params: types.CallToolRequestParams) -> types.CallToolResult:
        if params.name == "fixture_echo":
            text = ""
            if isinstance(params.arguments, dict):
                text = str(params.arguments.get("text", ""))
            payload = {"echo": text, "simulated": True, "source": "esab-fixture"}
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))],
                structured_content=payload,
                is_error=False,
            )
        if params.name == "fixture_fail":
            return types.CallToolResult(
                content=[types.TextContent(type="text", text="fixture upstream refused: simulated error")],
                is_error=True,
            )
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"unknown fixture tool {params.name}")],
            is_error=True,
        )

    async def on_list_resources(
        _ctx: object, _params: types.PaginatedRequestParams | None
    ) -> types.ListResourcesResult:
        return types.ListResourcesResult(
            resources=[
                types.Resource(
                    name="fixture-note",
                    uri="fixture://note",
                    description=SIMULATED,
                    mime_type="text/plain",
                )
            ]
        )

    async def on_read_resource(_ctx: object, params: types.ReadResourceRequestParams) -> types.ReadResourceResult:
        if str(params.uri) != "fixture://note":
            raise ValueError(f"unknown fixture resource {params.uri}")
        return types.ReadResourceResult(
            contents=[
                types.TextResourceContents(
                    uri="fixture://note",
                    mime_type="text/plain",
                    text="SIMULATED resource body",
                )
            ]
        )

    async def on_list_prompts(_ctx: object, _params: types.PaginatedRequestParams | None) -> types.ListPromptsResult:
        return types.ListPromptsResult(
            prompts=[
                types.Prompt(
                    name="fixture_prompt",
                    description=SIMULATED,
                    arguments=[types.PromptArgument(name="topic", description="模拟题目", required=True)],
                )
            ]
        )

    async def on_get_prompt(_ctx: object, params: types.GetPromptRequestParams) -> types.GetPromptResult:
        if params.name != "fixture_prompt":
            raise ValueError(f"unknown fixture prompt {params.name}")
        topic = (params.arguments or {}).get("topic", "")
        return types.GetPromptResult(
            description=SIMULATED,
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=f"SIMULATED prompt topic={topic}"),
                )
            ],
        )

    return Server(
        "esab-fixture",
        version="0.1.0",
        title="模拟上游",
        instructions=SIMULATED,
        on_list_tools=on_list_tools,
        on_call_tool=on_call_tool,
        on_list_resources=on_list_resources,
        on_read_resource=on_read_resource,
        on_list_prompts=on_list_prompts,
        on_get_prompt=on_get_prompt,
    )


async def serve_stdio() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    server = build_fixture_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def serve_http(port: int) -> None:
    import uvicorn

    server = build_fixture_server()
    app = server.streamable_http_app(host="127.0.0.1")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main() -> None:
    if "--http" in sys.argv:
        index = sys.argv.index("--http")
        port = int(sys.argv[index + 1])
        serve_http(port)
        return
    asyncio.run(serve_stdio())


if __name__ == "__main__":
    main()
