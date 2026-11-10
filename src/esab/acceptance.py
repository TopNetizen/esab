"""验收：标准 MCP 客户端经 stdio 桥接器调用标明为模拟的上游。

不连接真实工程软件，不调用任何会改模型的工具。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from esab.catalog import BRIDGE_TOOL_PREFIX


def _package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _child_env() -> dict[str, str]:
    root = str(_package_root())
    current = os.environ.get("PYTHONPATH", "")
    pythonpath = root if not current else root + os.pathsep + current
    return {"PYTHONPATH": pythonpath}


def write_fixture_config(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "id": "fixture",
                        "enabled": True,
                        "simulated": True,
                        "transport": "stdio",
                        "command": sys.executable,
                        "args": ["-m", "esab.fixture_upstream"],
                        "env": _child_env(),
                        "notes": "SIMULATED fixture. Not real software and not a structural calculation.",
                    }
                ]
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


async def subprocess_roundtrip(config: Path | None = None) -> dict[str, Any]:
    if config is None:
        config = Path.cwd() / ".acceptance-fixture.bridge.json"
    if not config.is_file():
        write_fixture_config(config)
    client = Client(
        StdioServerParameters(
            command=sys.executable,
            args=["-m", "esab", "stdio", "--config", str(config)],
            env=_child_env(),
        ),
        cache=None,
        mode="legacy",
    )
    async with client:
        listed = await client.list_tools(cache_mode="refresh")
        names = [tool.name for tool in listed.tools]
        echo_tool = next(tool for tool in listed.tools if tool.name == "fixture_echo")
        echo = await client.call_tool("fixture_echo", {"text": "stdio"})
        fail = await client.call_tool("fixture_fail", {})
        missing = await client.call_tool("RunStructAnalyse", {})
        resource = await client.read_resource("fixture://note", cache_mode="refresh")
        prompt = await client.get_prompt("fixture_prompt", {"topic": "stdio"})
        payload = echo.structured_content
        report = {
            "simulated": True,
            "real_software_called": False,
            "transport": "stdio",
            "tools": names,
            "fixture_echo_schema": echo_tool.input_schema,
            "echo": payload,
            "fail_is_error": fail.is_error,
            "fail_text": fail.content[0].text if fail.content else "",
            "missing_is_error": missing.is_error,
            "missing_text": missing.content[0].text if missing.content else "",
            "resource_text": resource.contents[0].text if resource.contents else "",
            "prompt_text": getattr(prompt.messages[0].content, "text", "") if prompt.messages else "",
        }
    report["ok"] = bool(
        "fixture_echo" in names
        and "fixture_fail" in names
        and "esab_status" in names
        and "esab_list_servers" in names
        and "RunStructAnalyse" not in names
        and "create_beam" not in names
        and isinstance(payload, dict)
        and payload.get("echo") == "stdio"
        and payload.get("simulated") is True
        and payload.get("source") == "esab-fixture"
        and fail.is_error
        and report["fail_text"] == "fixture upstream refused: simulated error"
        and missing.is_error
        and report["resource_text"] == "SIMULATED resource body"
        and report["prompt_text"] == "SIMULATED prompt topic=stdio"
        and all(name.startswith(BRIDGE_TOOL_PREFIX) or name.startswith("fixture_") for name in names)
    )
    return report


async def compare_with_direct_fixture() -> dict[str, Any]:
    """同一模拟上游，直连与经桥接后的 schema、返回和错误文本应一致。"""
    direct = Client(
        StdioServerParameters(
            command=sys.executable,
            args=["-m", "esab.fixture_upstream"],
            env=_child_env(),
        ),
        cache=None,
        mode="legacy",
    )
    config = Path.cwd() / ".acceptance-fixture.bridge.json"
    write_fixture_config(config)
    bridged = Client(
        StdioServerParameters(
            command=sys.executable,
            args=["-m", "esab", "stdio", "--config", str(config)],
            env=_child_env(),
        ),
        cache=None,
        mode="legacy",
    )
    async with direct, bridged:
        direct_tools = {tool.name: tool.model_dump(mode="json", exclude_none=True) for tool in (await direct.list_tools(cache_mode="refresh")).tools}
        bridge_tools = {tool.name: tool.model_dump(mode="json", exclude_none=True) for tool in (await bridged.list_tools(cache_mode="refresh")).tools}
        schema_equal = all(direct_tools[name] == bridge_tools[name] for name in direct_tools)
        echo_equal = (await direct.call_tool("fixture_echo", {"text": "对照"})).model_dump(mode="json", exclude_none=True) == (
            await bridged.call_tool("fixture_echo", {"text": "对照"})
        ).model_dump(mode="json", exclude_none=True)
        fail_equal = (await direct.call_tool("fixture_fail", {})).model_dump(mode="json", exclude_none=True) == (
            await bridged.call_tool("fixture_fail", {})
        ).model_dump(mode="json", exclude_none=True)
        resource_equal = (await direct.read_resource("fixture://note", cache_mode="refresh")).model_dump(mode="json", exclude_none=True) == (
            await bridged.read_resource("fixture://note", cache_mode="refresh")
        ).model_dump(mode="json", exclude_none=True)
        prompt_equal = (await direct.get_prompt("fixture_prompt", {"topic": "对照"})).model_dump(mode="json", exclude_none=True) == (
            await bridged.get_prompt("fixture_prompt", {"topic": "对照"})
        ).model_dump(mode="json", exclude_none=True)
    return {
        "simulated": True,
        "real_software_called": False,
        "schema_equal": schema_equal,
        "echo_equal": echo_equal,
        "fail_equal": fail_equal,
        "resource_equal": resource_equal,
        "prompt_equal": prompt_equal,
        "ok": schema_equal and echo_equal and fail_equal and resource_equal and prompt_equal,
    }


async def enumerate_readonly(url: str) -> dict[str, Any]:
    """对用户已经在监听的 MCP 地址做 tools/resources/prompts 列表。不调用工具。"""
    client = Client(url, cache=None, mode="legacy")
    async with client:
        tools = await client.list_tools(cache_mode="refresh")
        resources = await client.list_resources(cache_mode="refresh")
        prompts = await client.list_prompts(cache_mode="refresh")
    return {
        "url": url,
        "tools_called": False,
        "real_software_verified": False,
        "note": "只做了列表，没有调用工具，也不能证明结构设计结果正确。",
        "tools": [
            {"name": tool.name, "description": tool.description, "input_schema": tool.input_schema}
            for tool in tools.tools
        ],
        "resources": [{"name": item.name, "uri": str(item.uri)} for item in resources.resources],
        "prompts": [{"name": item.name, "description": item.description} for item in prompts.prompts],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="桥接器验收")
    parser.add_argument("--enumerate", metavar="URL", help="只读列出已有 MCP 服务，不调用工具")
    parser.add_argument("--compare", action="store_true", help="比较直连模拟上游与经桥接的结果")
    args = parser.parse_args(argv)
    if args.enumerate:
        report = asyncio.run(enumerate_readonly(args.enumerate))
    elif args.compare:
        report = asyncio.run(compare_with_direct_fixture())
    else:
        report = asyncio.run(subprocess_roundtrip())
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    Path("acceptance.log").write_text(text + "\n", encoding="utf-8")
    return 0 if report.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
