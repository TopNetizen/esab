"""MIDAS GEN NX REST 客户端。

MAPI-Key 只从环境变量读取，不写入日志。
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from esab.adapters.common import ConnectResult


class MidasError(RuntimeError):
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code


class MidasClient:
    def __init__(self, base_url: str, mapi_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._mapi_key = mapi_key

    def request(self, method: str, path: str, body: dict | None = None, timeout: float = 60) -> dict:
        if not path.startswith("/"):
            raise MidasError("使用 /db/NODE 这样的 API 路径，不要传完整 URL")
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            method=method.upper(),
            headers={
                "MAPI-Key": self._mapi_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise MidasError(f"HTTP {exc.code} {path}: {detail}", code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise MidasError(f"无法连接 GEN NX：{exc.reason}") from exc
        if not raw:
            return {}
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    def close(self) -> None:
        return None


def connect_midas() -> ConnectResult:
    evidence = "software_link_kit/midas.py 字符串：connect_midas、MAPI-Key、/db/NODE"
    base_url = os.environ.get("MIDAS_BASE_URL", "").strip()
    mapi_key = os.environ.get("MIDAS_MAPI_KEY", "").strip()
    if not base_url or not mapi_key:
        return ConnectResult(
            ok=False,
            software="MIDAS GEN NX",
            message=(
                "缺少 MIDAS_BASE_URL 或 MIDAS_MAPI_KEY。GEN NX 2026 起在 API Settings 里提供本机地址和密钥。"
                "密钥用 Windows DPAPI 存在配置中，本工具不读取、不打印该密钥。"
            ),
            evidence=evidence,
            entry="adapters.midas.connect_midas",
        )
    client = MidasClient(base_url, mapi_key)
    try:
        version = client.request("GET", "/config/ver")
    except MidasError as exc:
        return ConnectResult(
            ok=False,
            software="MIDAS GEN NX",
            message=str(exc),
            evidence=evidence,
            entry="adapters.midas.connect_midas",
        )
    return ConnectResult(
        ok=True,
        software="MIDAS GEN NX",
        message="已连接 GEN NX REST。",
        evidence=evidence,
        entry="adapters.midas.connect_midas",
        live_verified=True,
        injected=["midas"],
        details={"client": client, "version": version},
    )
