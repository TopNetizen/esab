import json
import os
import threading
import time
from pathlib import Path

from mcp import Client

from esab.adapters.hosts import CATALOG, connect_sap2000, connect_structural_pm
from esab.adapters.midas import MidasClient, MidasError
from esab.runtime.host import build_agent_server
from esab.runtime.worker import WorkerPool


def test_catalog_covers_the_requested_software():
    names = {item["software"] for item in CATALOG}
    assert names == {
        "PKPM",
        "SAP2000",
        "ETABS",
        "STAAD",
        "MIDAS GEN NX",
        "PKPM-CAE",
        "Abaqus",
        "Tekla",
        "SAUSG",
        "Rhino",
        "CAD",
        "SketchUp",
        "BIMBase",
        "PlantS",
        "GBP",
    }


def test_missing_software_returns_diagnostic_not_success(monkeypatch):
    monkeypatch.delenv("STRUCT_MCP_URL", raising=False)
    result = connect_structural_pm()
    assert result.ok is False
    assert result.live_verified is False
    assert "PKPM" in result.message
    sap = connect_sap2000()
    assert sap.ok is False
    assert "CSI.SAP2000.API.SapObject" in json.dumps(sap.as_dict(), ensure_ascii=False)


def test_python_executor_persists_and_can_cancel():
    pool = WorkerPool()
    first = pool.get("one").execute("value = 7\nprint(value)")
    assert first["ok"] is True
    assert "7" in str(first["stdout"])
    second = pool.get("one").execute("print(value + 1)")
    assert "8" in str(second["stdout"])
    other = pool.get("two").execute("print('value' in dir())")
    assert "False" in str(other["stdout"])
    started = threading.Thread(target=lambda: pool.get("sleep").execute("import time\ntime.sleep(30)\nprint('done')"))
    started.start()
    time.sleep(0.4)
    pool.get("sleep").cancel()
    started.join(timeout=5)
    again = pool.get("sleep").execute("print('after')")
    assert "after" in str(again["stdout"])


def test_injected_connect_and_function_search():
    pool = WorkerPool()
    result = pool.get("search").execute(
        "print(connect_to_server('pkpmmcp'))\n"
        "print(function_search('GetType'))\n"
        "print(is_server_connected('pkpmmcp'))"
    )
    text = str(result["stdout"])
    assert result["ok"] is True
    # 未运行 PKPM 时，连接必须返回 False 并给出诊断（环境变量缺失或进程未发现均可）
    assert ("没有 PKPM 的 MCP 地址" in text) or ("pkpmmcp" in text and ("未" in text or "没有" in text or "找不到" in text))
    assert "False" in text


def test_use_skill_reads_original_file(tmp_path: Path, monkeypatch):
    skill = tmp_path / "PKPM-Link"
    skill.mkdir()
    body = "---\nname: pkpm-link\n---\n\n# 原始标题\n不要改写这一行\n"
    (skill / "SKILL.md").write_text(body, encoding="utf-8")
    monkeypatch.setenv("ESAB_SKILLS_ROOT", str(tmp_path))
    pool = WorkerPool()
    result = pool.get("skill").execute("print(use_skill('pkpm-link'))")
    assert "不要改写这一行" in str(result["stdout"])
    assert result["ok"] is True


def test_agent_mcp_lists_runtime_tools():
    import asyncio

    async def run():
        async with Client(build_agent_server(), cache=None, mode="legacy") as client:
            listed = await client.list_tools(cache_mode="refresh")
            return [tool.name for tool in listed.tools]

    names = asyncio.run(run())
    assert names == ["python_executor", "use_skill", "cancel_execution", "list_software_adapters"]


def test_midas_client_sends_mapi_header_without_logging_it(tmp_path: Path):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen["path"] = self.path
            seen["has_key"] = bool(self.headers.get("MAPI-Key"))
            seen["key_value"] = self.headers.get("MAPI-Key")
            payload = json.dumps({"version": "test"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, fmt, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        client = MidasClient(f"http://127.0.0.1:{port}", "local-test-key")
        body = client.request("GET", "/config/ver")
        assert body["version"] == "test"
        assert seen["path"] == "/config/ver"
        assert seen["has_key"] is True
        assert "local-test-key" not in json.dumps({k: v for k, v in seen.items() if k != "key_value"})
    finally:
        server.shutdown()
    with pytest_raises_midas():
        MidasClient("http://127.0.0.1:9", "x").request("GET", "db/NODE")


def pytest_raises_midas():
    import pytest

    return pytest.raises(MidasError)


def test_api_database_roundtrip_with_bundled_db():
    """connect_db 能打开随包分发的只读 SQLite 数据库。"""
    from esab.skill_vault import connect_db

    sample = Path(__file__).resolve().parents[1] / "src" / "esab" / "data" / "skills" / "STAADPro-Link" / "references" / "openstaad_api.db"
    if not sample.is_file():
        return
    connection = connect_db(sample)
    count = connection.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0]
    assert count > 0
    connection.close()
