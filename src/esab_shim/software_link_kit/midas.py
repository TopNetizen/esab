"""MIDAS GEN NX REST API bridge."""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import urllib.request
import urllib.error


class MidasError(RuntimeError):
    pass


def detect_midas() -> dict:
    """Detect running MIDAS GEN NX process."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process -Name '*midas*','*GEN*' -ErrorAction SilentlyContinue | "
         "Select-Object -First 1 -ExpandProperty Path"],
        capture_output=True, text=True, timeout=10
    )
    path = result.stdout.strip()
    if not path:
        raise MidasError("MIDAS GEN NX is not running. Please start MIDAS and open a model.")
    return {"exe_path": path, "version": "unknown"}


def connect_midas(project_path: str | None = None, auto_start: bool = False) -> "MidasClient":
    """Connect to MIDAS GEN NX via REST API.

    MIDAS GEN NX exposes a REST API on localhost when running.
    """
    try:
        info = detect_midas()
    except MidasError:
        if project_path and auto_start:
            # TODO: start MIDAS with project
            raise MidasError("MIDAS not running. Please start MIDAS manually.")
        raise

    # MIDAS GEN NX REST API default port
    base_url = "http://127.0.0.1:8080"
    client = MidasClient(base_url)
    client._check()
    return client


class MidasClient:
    """REST API client for MIDAS GEN NX."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def _check(self):
        try:
            self._get("/db/UNIT")
        except Exception as e:
            raise MidasError(f"Cannot connect to MIDAS REST API: {e}")

    def _request(self, method: str, path: str, data: Any = None):
        url = self.base_url + path
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise MidasError(f"HTTP {e.code}: {e.read().decode()}")

    def _get(self, path: str):
        return self._request("GET", path)

    def get_nodes(self):
        return self._get("/db/NODE")

    def get_elements(self):
        return self._get("/db/ELEM")

    def get_units(self):
        return self._get("/db/UNIT")
