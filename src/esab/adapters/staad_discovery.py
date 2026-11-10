"""STAAD.Pro 与 openstaadpy 安装探测。

openstaadpy 是 Bentley 官方开源库（GitHub: BentleySystems/openstaadpy），
不在 PyPI 上公开发布，而是随 STAAD.Pro 2025+ 安装在：
    C:\\Program Files\\Bentley\\Engineering\\STAAD.Pro <year>\\STAAD\\OpenSTAADPy\\Setup\\openstaadpy-*.tar.gz
"""

from __future__ import annotations

import glob
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StaadInstall:
    version: str           # e.g. "2025", "2026"
    install_dir: Path      # e.g. C:\Program Files\Bentley\Engineering\STAAD.Pro 2025
    openstaadpy_tarball: Path | None  # the bundled openstaadpy-*.tar.gz, if present


def _year_from_dirname(name: str) -> str | None:
    m = re.search(r"(20\d{2})", name)
    return m.group(1) if m else None


def find_staad_installs() -> list[StaadInstall]:
    """枚举本机 STAAD.Pro 安装目录。Windows-only。"""
    results: list[StaadInstall] = []
    if sys.platform != "win32":
        return results

    candidates: list[Path] = []
    # 常见安装根
    for root in (
        r"C:\Program Files\Bentley\Engineering",
        r"C:\Program Files (x86)\Bentley\Engineering",
        r"C:\Program Files\Bentley",
    ):
        if os.path.isdir(root):
            try:
                for entry in os.listdir(root):
                    full = Path(root) / entry
                    if full.is_dir() and "STAAD" in entry.upper():
                        candidates.append(full)
            except OSError:
                pass

    # 注册表 HKLM\SOFTWARE\Bentley\STAADPro\
    try:
        import winreg
    except ImportError:
        winreg = None  # type: ignore
    if winreg is not None:
        for hive, sub in (
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Bentley\STAADPro"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Bentley\STAADPro"),
        ):
            try:
                with winreg.OpenKey(hive, sub) as key:
                    i = 0
                    while True:
                        try:
                            ver_name = winreg.EnumKey(key, i)
                            i += 1
                        except OSError:
                            break
                        try:
                            with winreg.OpenKey(key, ver_name) as vk:
                                install, _ = winreg.QueryValueEx(vk, "InstallPath")
                                candidates.append(Path(install))
                        except OSError:
                            continue
            except OSError:
                pass

    seen: set[Path] = set()
    for install_dir in candidates:
        try:
            resolved = install_dir.resolve()
        except OSError:
            resolved = install_dir
        if resolved in seen:
            continue
        seen.add(resolved)

        year = _year_from_dirname(str(install_dir)) or "unknown"
        tarball = _find_openstaadpy_tarball(resolved)
        results.append(StaadInstall(version=year, install_dir=resolved, openstaadpy_tarball=tarball))

    # 新版本优先
    results.sort(key=lambda s: s.version, reverse=True)
    return results


def _find_openstaadpy_tarball(install_dir: Path) -> Path | None:
    """在 STAAD.Pro 安装目录里找 OpenSTAADPy/Setup/openstaadpy-*.tar.gz。"""
    patterns = [
        str(install_dir / "STAAD" / "OpenSTAADPy" / "Setup" / "openstaadpy-*.tar.gz"),
        str(install_dir / "OpenSTAADPy" / "Setup" / "openstaadpy-*.tar.gz"),
        str(install_dir / "**" / "openstaadpy-*.tar.gz"),
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return Path(matches[0])
    return None


def ensure_openstaadpy_installed() -> tuple[bool, str]:
    """确保 openstaadpy 可 import。

    顺序：
      1. 已经能 import → (True, "already")
      2. 找到 STAAD.Pro 安装里的 tarball → pip install 它
      3. 都找不到 → (False, 提示信息)

    返回 (ok, message)。
    """
    try:
        import openstaadpy  # noqa: F401
        return True, "openstaadpy already importable"
    except ImportError:
        pass

    installs = find_staad_installs()
    for inst in installs:
        if inst.openstaadpy_tarball is not None:
            tarball = inst.openstaadpy_tarball
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", str(tarball)],
                    timeout=180,
                )
            except (subprocess.CalledProcessError, subprocess.SubprocessError) as exc:
                return False, f"pip install {tarball} 失败：{exc}"
            try:
                import openstaadpy  # noqa: F401
                return True, f"installed from {tarball}"
            except ImportError:
                return False, f"pip install 成功但仍无法 import openstaadpy（Python {sys.version_info.major}.{sys.version_info.minor} 可能不匹配）"

    available = "; ".join(str(i.install_dir) for i in installs) or "未找到任何 STAAD.Pro 安装"
    return False, (
        f"未找到 openstaadpy。本机 STAAD.Pro 探测结果：{available}。"
        "请安装 STAAD.Pro 2025+（自带 OpenSTAADPy/Setup/openstaadpy-*.tar.gz），"
        "或手动 pip install git+https://github.com/BentleySystems/openstaadpy.git。"
    )
