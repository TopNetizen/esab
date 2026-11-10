"""PlantS 连接。

原实现只查进程名就返回 connected=True：PlantS 进程在、但 MCP 服务没起来时
会假报连接成功，后续调用注入工具时才失败，错误位置与真实原因错位。
这里改为走与运行时一致的 MCP 端口发现 + 真实 initialize 握手。
"""
from __future__ import annotations


def connect_to_plants(*, project_path: str | None = None):
    """连接正在运行的 PlantS MCP，成功后上游工具已注入 python_executor。

    失败抛 RuntimeError，由调用方看到真实原因（进程未启动 / 端口无响应 / 握手失败）。
    """
    from esab.runtime.builtins import connect_to_plants as _real_connect

    outcome = _real_connect(project_path=project_path)
    if outcome is True:
        return {"connected": True, "via": "mcp-initialize"}
    raise RuntimeError(outcome)
