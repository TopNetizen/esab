"""SketchUp 自写桥接客户端。

对应 sketchup_bridge.rb（放到 SketchUp Plugins 目录的 Ruby 扩展）。
协议：4 字节大端长度前缀 + UTF-8 JSON body。
默认连接 127.0.0.1:49999。

不调用 esab_shim.software_link_kit.sketchup。
"""

from __future__ import annotations

import json
import os
import socket
import uuid
from typing import Any

from esab.adapters.common import ConnectResult

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 49999
MAX_BYTES = 64 * 1024 * 1024


class SketchUpError(RuntimeError):
    pass


class SketchUpClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 120.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def _request(self, method: str, **params: Any) -> dict:
        payload = {"id": str(uuid.uuid4()), "method": method, **params}
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(len(body).to_bytes(4, "big") + body)
            # 读 4 字节长度
            len_bytes = b""
            while len(len_bytes) < 4:
                chunk = sock.recv(4 - len(len_bytes))
                if not chunk:
                    raise SketchUpError("socket closed")
                len_bytes += chunk
            resp_len = int.from_bytes(len_bytes, "big")
            if resp_len > MAX_BYTES:
                raise SketchUpError(f"response too large: {resp_len}")
            data = b""
            while len(data) < resp_len:
                chunk = sock.recv(min(65536, resp_len - len(data)))
                if not chunk:
                    raise SketchUpError("socket closed mid-response")
                data += chunk
        resp = json.loads(data.decode("utf-8"))
        if not resp.get("ok", False):
            raise SketchUpError(resp.get("error", "unknown error"))
        return resp.get("result", {})

    def run(self, code: str, vars: dict | None = None, operation: str | None = None,
            timeout: float | None = None) -> Any:
        params: dict[str, Any] = {"code": code}
        if vars:
            params["vars"] = vars
        if operation:
            params["operation"] = operation
        return self._request("run", **params)

    def status(self) -> dict:
        return self._request("status")

    def summary(self) -> dict:
        return self._request("summary")


def connect_sketchup(path: str | None = None) -> ConnectResult:
    evidence = "自写 sketchup_bridge.rb：4 字节长度前缀 JSON，127.0.0.1:49999"
    host = os.environ.get("SKETCHUP_BRIDGE_HOST", DEFAULT_HOST)
    port = int(os.environ.get("SKETCHUP_BRIDGE_PORT", str(DEFAULT_PORT)))
    client = SketchUpClient(host, port)
    try:
        result = client.status()
    except (OSError, SketchUpError) as exc:
        return ConnectResult(
            ok=False,
            software="SketchUp",
            message=(
                f"无法连接 SketchUp 桥接插件 {host}:{port}（{exc}）。"
                "请确认：1) SketchUp 已打开；2) sketchup_bridge.rb 已放到 Plugins 目录并重启 SketchUp。"
            ),
            evidence=evidence,
            entry="adapters.sketchup_client.connect_sketchup",
        )
    return ConnectResult(
        ok=True,
        software="SketchUp",
        message="SketchUp 桥接插件已连接。",
        evidence=evidence,
        entry="adapters.sketchup_client.connect_sketchup",
        live_verified=True,
        injected=["su"],
        details={"client": client, "status": result, "path": path},
    )
