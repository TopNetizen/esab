"""单个 Python 工作进程里的连接和检索状态。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BoundTool:
    server_name: str
    name: str
    description: str
    input_schema: dict[str, Any]
    category: str
    call: Callable[..., Any]


@dataclass
class RuntimeState:
    connections: dict[str, dict[str, Any]] = field(default_factory=dict)
    tools: dict[str, BoundTool] = field(default_factory=dict)
    classes: dict[str, str] = field(default_factory=dict)
    user_namespace: dict[str, Any] | None = None
    skills_root: str | None = None
    agent_home: str | None = None

    def categories(self) -> list[str]:
        found = {tool.category for tool in self.tools.values()}
        return sorted(found)

    def search(self, action: str, func_type: str = "", func_names: list[str] | None = None) -> Any:
        action = (action or "").strip()
        if action == "GetType":
            return self.categories()
        if action == "GetClass":
            return self.classes
        if action == "GetName":
            return [
                tool.name
                for tool in self.tools.values()
                if not func_type or tool.category == func_type or tool.server_name == func_type
            ]
        if action == "GetDescription":
            wanted = set(func_names or [])
            rows = []
            for tool in self.tools.values():
                if func_type and tool.category != func_type and tool.server_name != func_type:
                    continue
                if wanted and tool.name not in wanted:
                    continue
                rows.append(
                    {
                        "name": tool.name,
                        "category": tool.category,
                        "server": tool.server_name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                    }
                )
            return rows
        raise ValueError(
            "function_search 的 action 只接受 GetType、GetName、GetDescription、GetClass。"
            "这四项来自桥接器的 MCP 系统提示。"
        )


STATE = RuntimeState()
