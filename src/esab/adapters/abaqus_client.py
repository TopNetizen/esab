"""Abaqus 内核桥客户端。

127.0.0.1:48152，一行一个 JSON，方法 ping / health / execute。
不启动 Abaqus，也不触碰许可。
"""

from __future__ import annotations

import json
import os
import socket
import uuid
from typing import Any

from esab.adapters.common import ConnectResult

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 48152


def send_json_message(sock: socket.socket, payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    sock.sendall(data + b"\n")


def recv_json_message(sock: socket.socket, max_bytes: int = 16 * 1024 * 1024) -> dict[str, Any]:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise RuntimeError("socket closed before a complete message was received")
        newline = chunk.find(b"\n")
        if newline >= 0:
            total += newline
            if total > max_bytes:
                raise RuntimeError(f"message exceeded {max_bytes} bytes")
            chunks.append(chunk[:newline])
            break
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise RuntimeError(f"message exceeded {max_bytes} bytes")
    message = json.loads(b"".join(chunks).decode("utf-8"))
    if not isinstance(message, dict):
        raise RuntimeError("protocol message must be a JSON object")
    return message


class AbaqusBridgeClient:
    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 30.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        request_params = dict(params or {})
        request_params.setdefault("timeout", self.timeout)
        payload = {"id": str(uuid.uuid4()), "method": method, "params": request_params}
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            send_json_message(sock, payload)
            response = recv_json_message(sock)
        if response.get("id") != payload["id"]:
            raise RuntimeError("Abaqus runtime returned a mismatched response id")
        if not response.get("ok", False):
            error = response.get("error") or {}
            message = error.get("message") if isinstance(error, dict) else str(error)
            raise RuntimeError(message or "Abaqus runtime returned an error")
        result = response.get("result")
        if not isinstance(result, dict):
            raise RuntimeError("Abaqus runtime returned an invalid result envelope")
        return result

    def health(self) -> dict[str, Any]:
        return self.request("health")

    def execute(self, code: str, work_dir: str | None = None, timeout: float | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"code": code, "response_mode": "normal"}
        if work_dir is not None:
            params["work_dir"] = work_dir
        if timeout is not None:
            params["timeout"] = timeout
        return self.request("execute", params)


def connect_abaqus(workspace_dir: str) -> ConnectResult:
    evidence = "abaqus/kernel/bridge_client.py 与 kernel_bridge.py：127.0.0.1:48152 换行 JSON"
    host = os.environ.get("STRUCT_ABAQUS_HOST", DEFAULT_HOST)
    port = int(os.environ.get("STRUCT_ABAQUS_PORT", str(DEFAULT_PORT)))
    client = AbaqusBridgeClient(host, port)
    try:
        health = client.health()
    except OSError as exc:
        return ConnectResult(
            ok=False,
            software="Abaqus",
            message=(
                f"没有连上 {host}:{port}（{exc}）。"
                "请先把 esab 自带的 adapters/abaqus_plugin.py 复制到 AbaqusPlugins 目录，"
                "然后启动 Abaqus/CAE。本客户端只附着该端口，不启动 Abaqus，也不检查许可证。"
            ),
            evidence=evidence,
            entry="adapters.abaqus_client.connect_abaqus",
            details={"host": host, "port": port},
        )
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software="Abaqus",
            message=f"{type(exc).__name__}: {exc}",
            evidence=evidence,
            entry="adapters.abaqus_client.connect_abaqus",
        )
    return ConnectResult(
        ok=True,
        software="Abaqus",
        message="Abaqus 内核桥 health 已返回。",
        evidence=evidence,
        entry="adapters.abaqus_client.connect_abaqus",
        live_verified=True,
        injected=["abaqus"],
        details={"health": health, "client": client, "workspace_dir": workspace_dir},
    )
