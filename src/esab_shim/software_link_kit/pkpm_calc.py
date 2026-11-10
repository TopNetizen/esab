"""PKPM calculation bridge (MCP-based)."""
from __future__ import annotations

from esab.adapters.hosts import connect_structural_pm


def connect_pkpm_calc():
    """连接 PKPM MCP，返回注入后的函数命名空间。

    原实现取 ``details["value"]``，但 MCP 路径的 details 只有
    url / pages / namespace，取不到就静默返回 None——上层拿到 None 才报错，
    来源已经查不清。这里改成：取不到对象就直接抛出，并把 details 里的键打印出来。
    """
    result = connect_structural_pm()
    if not result.ok:
        raise RuntimeError(result.message)
    details = result.details or {}
    value = details.get("value")
    if value is None:
        value = details.get("namespace")
    if not value:
        raise RuntimeError(
            f"PKPM 已连接但取不到可调用对象；details 里现有键：{sorted(details)}。"
        )
    return value
