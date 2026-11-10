"""主机侧诊断。只做只读核对，不启动目标软件，不调用会改模型的工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_desktop_marker(path: Path) -> dict[str, Any]:
    """读取桌面标记文件的安装路径。token 字段永不返回。"""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("桌面标记文件不是对象")
    result: dict[str, Any] = {"path": raw.get("path")}
    if "token" in raw:
        result["token_present"] = True
        result["token"] = None
    else:
        result["token_present"] = False
    return result


def redact_mapping(raw: dict[str, Any]) -> dict[str, Any]:
    hidden = {"token", "authorization", "api_key", "apikey", "secret", "password"}
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        if key.lower() in hidden or "token" in key.lower() or "secret" in key.lower():
            cleaned[key] = None
            cleaned[f"{key}_present"] = value not in (None, "")
            continue
        if isinstance(value, dict):
            cleaned[key] = redact_mapping(value)
        else:
            cleaned[key] = value
    return cleaned
