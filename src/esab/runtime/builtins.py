"""注入到持久 Python 环境的函数。名字与桥接器技能和系统提示一致。"""

from __future__ import annotations

import io
import traceback
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

from esab.adapters.hosts import CONNECTORS, connect_plants
from esab.adapters.mcp_upstream import disconnect
from esab.runtime import skills_api
from esab.runtime.state import STATE


def connect_to_server(server_name: str, work_dir: str | None = None, cmd_args: str | None = None) -> bool | str:
    connector = CONNECTORS.get(server_name)
    if connector is None:
        known = ", ".join(sorted(CONNECTORS))
        return f"没有名为 {server_name} 的连接入口。已知：{known}"
    result = connector(work_dir=work_dir, cmd_args=cmd_args)
    if result.ok:
        _publish(result.server_name or server_name, result.details.get("namespace"))
        return True
    return result.message


def connect_to_plants(project_path: str | None = None, exe_path: str | None = None) -> bool | str:
    del exe_path
    result = connect_plants(work_dir=project_path)
    if result.ok:
        _publish("plantsmcp", result.details.get("namespace"))
        return True
    return result.message


def connect_cad(cad_type: str | None = None, visible: bool = True):
    """连接本机 CAD（AutoCAD / 浩辰 / 中望），返回 pyautocad 兼容的 acad 对象。

    连接成功打印一行简报；失败直接抛异常，不做惰性假成功。
    """
    from esab_shim.cad import connect_cad as _connect

    acad, info = _connect(cad_type=cad_type, visible=visible)
    print(f"已连接 {info['product']} {info['version']}：{info['document']}（{info['progid']}）")
    return acad


def disconnect_server(server_name: str) -> bool:
    disconnect(server_name)
    return True


def is_server_connected(server_name: str) -> bool:
    return bool(STATE.connections.get(server_name, {}).get("ok"))


def function_search(action: str, func_type: str = "", func_names: list[str] | None = None) -> Any:
    return STATE.search(action, func_type, func_names)


def use_skill(name: str, file: str | None = None, run: str | None = None, run_args: str = "") -> str:
    return skills_api.use_skill(name, file=file, run=run, run_args=run_args)


def install(namespace: dict[str, Any]) -> None:
    STATE.user_namespace = namespace
    namespace["connect_to_server"] = connect_to_server
    namespace["disconnect_server"] = disconnect_server
    namespace["is_server_connected"] = is_server_connected
    namespace["function_search"] = function_search
    namespace["use_skill"] = use_skill
    namespace["connect_to_plants"] = connect_to_plants
    namespace["connect_cad"] = connect_cad
    namespace["STATE"] = STATE


def execute(code: str, namespace: dict[str, Any]) -> dict[str, Any]:
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            exec(code, namespace, namespace)  # noqa: S102 - 持久执行环境是技能的使用方式
        return {"ok": True, "stdout": buffer.getvalue(), "error": ""}
    except Exception:
        return {"ok": False, "stdout": buffer.getvalue(), "error": traceback.format_exc()}


def _publish(server_name: str, namespace: dict[str, Any] | None) -> None:
    if not isinstance(namespace, dict):
        return
    target = STATE.connections.setdefault(server_name, {})
    target["namespace"] = namespace
    if isinstance(STATE.user_namespace, dict):
        STATE.user_namespace.update(namespace)


def skill_root() -> Path | None:
    if STATE.skills_root:
        return Path(STATE.skills_root)
    return None
