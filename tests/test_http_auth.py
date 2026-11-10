import asyncio
import os
import socket
import sys
from pathlib import Path

import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from esab.acceptance import write_fixture_config
from esab.cli import _reject_remote


def test_http_refuses_non_loopback_by_default():
    with pytest.raises(SystemExit):
        _reject_remote("0.0.0.0", allow_remote=False)
    _reject_remote("127.0.0.1", allow_remote=False)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_http_requires_bearer_and_forwards_fixture():
    async def run():
        port = _free_port()
        config = Path.cwd() / f".test-http-{port}.bridge.json"
        write_fixture_config(config)
        token = "bridge-test-token"
        env = os.environ.copy()
        src = str(Path(__file__).resolve().parents[1] / "src")
        env["PYTHONPATH"] = src if "PYTHONPATH" not in env else src + os.pathsep + env["PYTHONPATH"]
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "esab",
            "http",
            "--config",
            str(config),
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--token",
            token,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        url = f"http://127.0.0.1:{port}/mcp"
        try:
            await _wait_port(port)
            denied = await _probe(url, None)
            allowed = await _probe(url, token)
            return denied, allowed
        finally:
            process.terminate()
            await process.wait()

    denied, allowed = asyncio.run(run())
    assert denied["status"] == 401
    assert allowed["ok"] is True
    assert allowed["echo"]["simulated"] is True
    assert "create_beam" not in allowed["names"]


async def _wait_port(port: int) -> None:
    for _ in range(50):
        try:
            _reader, writer = await asyncio.open_connection("127.0.0.1", port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError:
            await asyncio.sleep(0.1)
    raise RuntimeError("HTTP 桥接器没有在预期时间内开始监听")


async def _probe(url: str, token: str | None) -> dict:
    headers = {"Authorization": f"Bearer {token}"} if token else None
    if token is None:
        async with create_mcp_http_client() as http:
            response = await http.post(url, json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            return {"status": response.status_code}
    async with create_mcp_http_client(headers=headers) as http:
        async with streamable_http_client(url, http_client=http) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listed = await session.list_tools()
                echo = await session.call_tool("fixture_echo", {"text": "http"})
                return {
                    "ok": True,
                    "names": [tool.name for tool in listed.tools],
                    "echo": echo.structured_content,
                }
