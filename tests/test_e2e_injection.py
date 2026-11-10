import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait(port: int) -> None:
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("模拟 MCP 没有开始监听")


def test_executor_connects_fixture_and_calls_injected_tool(monkeypatch, tmp_path: Path):
    port = _free_port()
    env = os.environ.copy()
    env["FIXTURE_PAGINATE"] = "1"
    src = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    process = subprocess.Popen(
        [sys.executable, "-m", "esab.fixture_upstream", "--http", str(port)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait(port)
        monkeypatch.setenv("STRUCT_MCP_URL", f"http://127.0.0.1:{port}/mcp")
        from esab.runtime.worker import WorkerPool

        pool = WorkerPool()
        code = (
            "result = connect_to_server('pkpmmcp')\n"
            "print('CONNECTED', result)\n"
            "names = function_search('GetName', func_type='pkpmmcp')\n"
            "print('NAMES', sorted(names))\n"
            "print('ECHO', fixture_echo(text='e2e'))\n"
            "try:\n"
            "    fixture_fail()\n"
            "except Exception as exc:\n"
            "    print('FAIL', type(exc).__name__, exc)\n"
        )
        result = pool.get("e2e").execute(code, timeout=30)
    finally:
        process.kill()
        process.wait(timeout=5)
    text = str(result["stdout"])
    assert result["ok"] is True, result
    assert "CONNECTED True" in text
    assert "fixture_echo" in text and "fixture_fail" in text
    assert "'echo': 'e2e'" in text or '"echo": "e2e"' in text
    assert "simulated" in text
    assert "fixture upstream refused: simulated error" in text


def test_redact_removes_mapi_key(monkeypatch):
    from esab.adapters.common import redact

    monkeypatch.setenv("MIDAS_MAPI_KEY", "super-secret-mapi")
    assert "super-secret-mapi" not in redact("header super-secret-mapi failed")


def test_cancel_does_not_claim_software_stopped():
    import asyncio

    from mcp import Client
    from esab.runtime.host import build_agent_server

    async def run():
        async with Client(build_agent_server(), cache=None, mode="legacy") as client:
            result = await client.call_tool("cancel_execution", {"session_id": "none"})
            return result.content[0].text

    text = asyncio.run(run())
    payload = json.loads(text)
    assert payload["worker_terminated"] is True
    assert payload["software_operation_cancelled"] is False
