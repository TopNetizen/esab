"""PKPM installation detection."""
from __future__ import annotations

import os
import winreg
from pathlib import Path


def find_pkpm_install() -> Path | None:
    """Find PKPM installation directory."""
    candidates = [
        r"C:\Program Files\PKPM",
        r"D:\Program Files\PKPM",
        r"C:\PKPM",
        r"D:\PKPM",
    ]
    for path in candidates:
        if Path(path).is_dir():
            return Path(path)

    # Try registry
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\PKPM")
        install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
        winreg.CloseKey(key)
        return Path(install_dir)
    except OSError:
        pass

    return None
