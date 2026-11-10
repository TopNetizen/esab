"""动态发现本地 MCP server 端口。

1. 按进程名找到目标软件的 PID。
2. 用 iphelper 枚举该 PID 持有的 LISTENING TCP 端口。
3. 对每个端口发一次 MCP Streamable HTTP initialize 握手，回应正确的即 MCP server。

只需要目标软件已由用户手动启动。
"""

from __future__ import annotations

import json
import socket
import subprocess
import time
from dataclasses import dataclass, field
from typing import Iterator

# ---------------------------------------------------------------------------
# 进程名映射
# ---------------------------------------------------------------------------

PROCESS_NAMES: dict[str, tuple[str, ...]] = {
    "pkpmmcp": ("PKPMMain.exe", "PKPM.exe"),
    "cae-mcp": ("PKPMCAE.exe", "PyPCAE.exe", "CAEMain.exe"),
    "ssgmcp": ("SAUSAGE.exe", "SAUSGZeta.exe", "SAUSGPI.exe", "SAUSGJG.exe", "OpenSAUSG.exe"),
    "plantsmcp": ("BIMBase.exe", "PlantS.exe", "P3D.exe"),
    "BIMBaseAI2PY_MCPServer": ("BIMBase.exe", "PKPMBIM.exe"),
}

# GBP 已知固定端口，不需要探测
FIXED_URLS: dict[str, str] = {
    "gbpmcp": "http://127.0.0.1:3333/GBPBECA3/galpserver/mcp",
}

# 端口发现结果缓存：server_name -> (pid, port, discovered_at)
_cache: dict[str, tuple[int, int, float]] = {}


@dataclass
class DiscoveryResult:
    server_name: str
    url: str | None = None
    pid: int | None = None
    port: int | None = None
    candidates: list[int] = field(default_factory=list)
    error: str | None = None


# ---------------------------------------------------------------------------
# 进程枚举
# ---------------------------------------------------------------------------


def _running_pids(process_names: tuple[str, ...]) -> list[int]:
    """返回指定进程名的所有 PID。Windows 用 tasklist，跨平台回退 psutil。"""
    # 优先 tasklist（Windows 内置，无额外依赖）
    try:
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        output = ""

    names_lower = {n.lower() for n in process_names}
    pids: list[int] = []
    for line in output.splitlines():
        parts = line.strip().strip('"').split('","')
        if len(parts) >= 2:
            exe_name = parts[0].strip().lower()
            if exe_name in names_lower:
                try:
                    pids.append(int(parts[1]))
                except ValueError:
                    pass
    if pids:
        return pids

    # 回退：psutil（如果安装了）
    try:
        import psutil  # type: ignore

        for proc in psutil.process_iter(["pid", "name"]):
            if (proc.info.get("name") or "").lower() in names_lower:
                pids.append(proc.info["pid"])
    except ImportError:
        pass
    return pids


# ---------------------------------------------------------------------------
# 枚举 PID 持有的 LISTENING TCP 端口
# ---------------------------------------------------------------------------


def _listening_ports_for_pid(pid: int) -> list[int]:
    """返回该 PID 正在 LISTEN 的 TCP 端口。Windows 用 netstat -ano。"""
    try:
        output = subprocess.check_output(
            ["netstat", "-ano", "-p", "TCP"],
            text=True,
            timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return []

    ports: set[int] = set()
    target = str(pid)
    for line in output.splitlines():
        parts = line.split()
        # 协议 本地地址 外部地址 状态 PID
        # TCP    127.0.0.1:48152    0.0.0.0:0    LISTENING    12345
        if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING":
            if parts[4] == target:
                local = parts[1]
                if ":" in local:
                    port_str = local.rsplit(":", 1)[-1]
                    try:
                        ports.add(int(port_str))
                    except ValueError:
                        pass
    return sorted(ports)


# ---------------------------------------------------------------------------
# MCP Streamable HTTP 握手探测
# ---------------------------------------------------------------------------


def _probe_mcp(host: str, port: int, timeout: float = 2.5) -> bool:
    """对 host:port 发送一次 MCP initialize，判断是否为 MCP server。

    MCP Streamable HTTP 传输：POST /mcp，Content-Type: application/json,
    Accept: application/json, text/event-stream。
    Body 是 JSON-RPC 2.0 initialize 请求。
    """
    import urllib.request
    import urllib.error

    body = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "esab", "version": "0.4.0"},
        },
    }).encode("utf-8")

    url = f"http://{host}:{port}/mcp"
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            # 200 或 406（不接受 SSE）都说明这是个 HTTP 服务且认识 MCP 路径
            if status in (200, 406):
                return True
            # 读一点 body 看是否有 MCP 特征
            chunk = resp.read(4096).decode("utf-8", "replace")
            if "jsonrpc" in chunk or "MCP" in chunk or "serverInfo" in chunk:
                return True
    except urllib.error.HTTPError as exc:
        # 406/400 通常意味着路径存在但参数不接受，也是 MCP 特征
        if exc.code in (400, 405, 406, 401, 403):
            try:
                chunk = exc.read(4096).decode("utf-8", "replace")
                if "jsonrpc" in chunk or "mcp" in chunk.lower() or "initialize" in chunk:
                    return True
            except Exception:
                pass
            # 401/403 也可能是 MCP server 要求 token——对本地回环先算命中
            if exc.code in (401, 403):
                return True
    except (OSError, socket.timeout):
        pass
    return False


# ---------------------------------------------------------------------------
# 主发现入口
# ---------------------------------------------------------------------------


def discover_mcp_url(
    server_name: str,
    env_url: str = "",
    host: str = "127.0.0.1",
    probe_timeout: float = 2.5,
) -> DiscoveryResult:
    """发现某个 MCP server 的 URL。

    优先级：
    1. env_url（用户通过环境变量显式指定）——直接用，不探测。
    2. 缓存命中且 PID 仍在——直接用。
    3. FIXED_URLS 中的固定地址。
    4. 动态探测：找进程 → 枚举端口 → MCP 握手。
    """
    if env_url:
        return DiscoveryResult(server_name=server_name, url=env_url)

    # 固定 URL
    if server_name in FIXED_URLS:
        return DiscoveryResult(server_name=server_name, url=FIXED_URLS[server_name])

    # 缓存
    if server_name in _cache:
        pid, port, ts = _cache[server_name]
        if pid in _running_pids(PROCESS_NAMES.get(server_name, ())):
            return DiscoveryResult(
                server_name=server_name,
                url=f"http://{host}:{port}/mcp",
                pid=pid,
                port=port,
            )
        # 进程不在了，清缓存
        del _cache[server_name]

    proc_names = PROCESS_NAMES.get(server_name)
    if not proc_names:
        return DiscoveryResult(
            server_name=server_name,
            error=f"未知的 MCP 服务名 {server_name}，且没有环境变量提供 URL。",
        )

    pids = _running_pids(proc_names)
    if not pids:
        return DiscoveryResult(
            server_name=server_name,
            error=(
                f"没有找到运行中的 {server_name} 进程（查找 {', '.join(proc_names)}）。"
                "请先打开已授权的软件。"
            ),
        )

    # 收集所有候选端口
    all_ports: set[int] = set()
    for pid in pids:
        for port in _listening_ports_for_pid(pid):
            all_ports.add(port)

    if not all_ports:
        return DiscoveryResult(
            server_name=server_name,
            candidates=[],
            error=(
                f"找到进程 {server_name}（PID {pids[0]}）但没有它监听的 TCP 端口。"
                "软件可能还没启动 MCP 服务，请稍等再试。"
            ),
        )

    # 探测：优先高端口（MCP 通常不用 80/443/3389 这些常见端口）
    candidates = sorted(all_ports, reverse=True)
    for port in candidates:
        if _probe_mcp(host, port, timeout=probe_timeout):
            # 缓存到第一个仍在运行的 PID
            _cache[server_name] = (pids[0], port, time.time())
            return DiscoveryResult(
                server_name=server_name,
                url=f"http://{host}:{port}/mcp",
                pid=pids[0],
                port=port,
                candidates=candidates,
            )

    return DiscoveryResult(
        server_name=server_name,
        candidates=candidates,
        error=(
            f"找到 {server_name} 进程（PID {pids[0]}）的 {len(candidates)} 个监听端口，"
            f"但没有一个响应 MCP initialize 握手。候选端口：{candidates[:20]}。"
            "软件可能还在启动中，或 MCP 服务未启用。"
        ),
    )


def invalidate(server_name: str | None = None) -> None:
    """清除端口发现缓存。传 None 清全部。"""
    if server_name is None:
        _cache.clear()
    else:
        _cache.pop(server_name, None)
