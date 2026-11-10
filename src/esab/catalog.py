"""内置 MCP 服务目录。

只记录连接各工程软件所需的服务 id、URL 模式和进程名。
"""

from __future__ import annotations

from typing import Any

BUILTIN_SERVERS: list[dict[str, Any]] = [
    {
        "id": "pkpmmcp",
        "nickname": "结构主线",
        "description": "三维主线建模模块",
        "transport": "streamable_http",
        "url": None,
        "url_pattern": "http://127.0.0.1:{port}/mcp",
        "host_process": "PKPMMain.exe",
    },
    {
        "id": "stsmcp",
        "nickname": "钢结构",
        "description": "二维钢结构模块",
        "transport": "streamable_http",
        "url": None,
        "url_pattern": "http://127.0.0.1:{port}/mcp",
    },
    {
        "id": "jccadmcp",
        "nickname": "基础",
        "description": "基础设计模块",
        "transport": "streamable_http",
        "url": None,
        "url_pattern": "http://127.0.0.1:{port}/mcp",
    },
    {
        "id": "gbpmcp",
        "nickname": "绿色低碳",
        "description": "节能与碳排放计算模块",
        "transport": "streamable_http",
        "url": "http://127.0.0.1:3333/GBPBECA3/galpserver/mcp",
    },
    {
        "id": "cae-mcp",
        "nickname": "通用仿真",
        "description": "多物理场耦合仿真",
        "transport": "streamable_http",
        "url": None,
    },
    {
        "id": "plantsmcp",
        "nickname": "PlantS",
        "description": "三维工厂结构设计",
        "transport": "streamable_http",
        "url": None,
        "url_pattern": "http://127.0.0.1:{port}/mcp",
        "host_process": "BIMBase.exe",
    },
    {
        "id": "ssgmcp",
        "nickname": "SAUSG",
        "description": "非线性弹塑性分析",
        "transport": "streamable_http",
        "url": None,
        "url_pattern": "http://localhost:{port}/mcp",
    },
    {
        "id": "BIMBaseAI2PY_MCPServer",
        "nickname": "BIMBase 参数化组件",
        "description": "Python 参数化建模",
        "transport": "streamable_http",
        "url": None,
    },
]

BRIDGE_TOOL_PREFIX = "esab_"
UPSTREAM_NAME_SEPARATOR = "__"

SUPPORTED_UPSTREAM_TRANSPORTS = ("stdio", "streamable_http")
