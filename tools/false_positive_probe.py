# -*- coding: utf-8 -*-
"""针对性证伪：验证可疑判据是否会导致假成功。"""
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

print("=" * 70)
print("[A] 假 MCP 服务：200 + 像模像样的 JSON-RPC，能不能骗过 connect_streamable")
print("=" * 70)


class FakeMCP(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {"name": "fake"}}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


sock = socket.socket()
sock.bind(("127.0.0.1", 0))
port = sock.getsockname()[1]
sock.close()
server = HTTPServer(("127.0.0.1", port), FakeMCP)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{port}/mcp"
print(f"假服务已启动: {url}")

from esab.adapters.port_discovery import _probe_mcp
print(f"  port_discovery._probe_mcp 判定为 MCP: {_probe_mcp('127.0.0.1', port, timeout=3)}")

from esab.adapters.mcp_upstream import connect_streamable
r = connect_streamable("fake", url, "FakeSoftware", "test")
print(f"  connect_streamable ok={r.ok} live={r.live_verified}")
print(f"  message: {r.message[:200]}")
server.shutdown()

print()
print("=" * 70)
print("[B] connect_official：官方包装返回错误字符串时会不会被当成成功")
print("=" * 70)
from esab.adapters.hosts import connect_official

r2 = connect_official("json", "dumps", "FakeSW", "test", obj={"a": 1})
print(f"  函数返回字符串 '{'{\"a\": 1}'}' → ok={r2.ok} live={r2.live_verified} message={r2.message}")

print()
print("=" * 70)
print("[C] PlantS 包装层：只看进程名就 connected=True")
print("=" * 70)
from esab_shim.software_link_kit import plants as plants_shim

_real_run = plants_shim.subprocess.run


class FakeCompleted:
    stdout = "C:\\Program Files\\BIMBase\\BIMBase.exe\n"


plants_shim.subprocess.run = lambda *a, **k: FakeCompleted()
try:
    print(f"  伪造进程存在（其实没有任何 PlantS 实例）→ {plants_shim.connect_to_plants()}")
finally:
    plants_shim.subprocess.run = _real_run

print()
print("=" * 70)
print("[D] pkpm_calc：连接成功但取不到对象")
print("=" * 70)
import inspect
from esab_shim.software_link_kit import pkpm_calc

print("  代码：", inspect.getsource(pkpm_calc.connect_pkpm_calc).strip().replace("\n", " | "))
from esab.adapters.hosts import connect_structural_pm
res = connect_structural_pm()
print(f"  本机 connect_structural_pm ok={res.ok}, details 键={list((res.details or {}).keys())}")
print("  → details 里没有 'value'，pkpm_calc 会返回 None 而不报错")
