import asyncio
from pathlib import Path

from mcp import Client

from esab.acceptance import compare_with_direct_fixture, subprocess_roundtrip
from esab.config import ServerSpec
from esab.server import build_server


def test_stdio_client_bridge_fixture_roundtrip():
    report = asyncio.run(subprocess_roundtrip(Path.cwd() / ".test-fixture.bridge.json"))
    assert report["ok"], report
    assert report["real_software_called"] is False
    assert report["echo"]["simulated"] is True


def test_bridge_preserves_fixture_schema_result_and_error():
    report = asyncio.run(compare_with_direct_fixture())
    assert report["ok"], report


def test_down_upstream_does_not_invent_pkpm_tools():
    async def run():
        server = build_server(
            [
                ServerSpec(
                    id="pkpmmcp",
                    enabled=True,
                    transport="stdio",
                    command="definitely-missing-pkpm-host",
                    simulated=False,
                )
            ]
        )
        async with Client(server, cache=None, mode="legacy") as client:
            listed = await client.list_tools(cache_mode="refresh")
            names = [tool.name for tool in listed.tools]
            missing = await client.call_tool("create_beam", {"b": 300})
            status = await client.call_tool("esab_status", {})
            return names, missing, status

    names, missing, status = asyncio.run(run())
    assert names == ["esab_status", "esab_list_servers"]
    assert missing.is_error
    assert "create_beam" not in missing.content[0].text or "没有名为" in missing.content[0].text
    assert "definitely-missing-pkpm-host" in status.content[0].text or "FileNotFound" in status.content[0].text or "Error" in status.content[0].text
