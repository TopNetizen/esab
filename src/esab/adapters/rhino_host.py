"""Rhino COM 连接。

1. 读注册表探测已装版本
2. 用 gencache.EnsureDispatch 做 typelib 早期绑定
3. 无运行实例时按最高版本启动 Rhino.exe
4. GetScriptObject() 拿 IRhinoScript
5. 提供 VARIANT marshalling 辅助函数
返回 (rhino, script, version_int) 三元组，与签名一致。
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Any

from esab.adapters.common import ConnectResult

EVIDENCE = (
    "Rhino-Link 技能：get_rhino() 读注册表探测版本、gencache 早期绑定、"
    "GetScriptObject() 返回 (rhino, script, version)；VARIANT 辅助函数语义来自技能文档"
)


# ---------------------------------------------------------------------------
# 注册表版本探测
# ---------------------------------------------------------------------------


def _installed_rhino_versions() -> list[tuple[int, str]]:
    """从注册表返回 [(major_version, install_dir)]，按版本降序。"""
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:
        return []

    found: list[tuple[int, str]] = []
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\McNeel\Rhinoceros"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\McNeel\Rhinoceros"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\McNeel\Rhinoceros"),
    ]
    for hive, base in roots:
        try:
            with winreg.OpenKey(hive, base) as root:
                i = 0
                while True:
                    try:
                        ver_key_name = winreg.EnumKey(root, i)
                        i += 1
                    except OSError:
                        break
                    # ver_key_name 形如 "8.0"
                    parts = ver_key_name.split(".")
                    try:
                        major = int(parts[0])
                    except (ValueError, IndexError):
                        continue
                    try:
                        with winreg.OpenKey(root, ver_key_name) as ver_key:
                            # InstallPath 或 5.00 子键下的 InstallPath
                            install_dir = ""
                            try:
                                install_dir, _ = winreg.QueryValueEx(ver_key, "InstallPath")
                            except OSError:
                                # 尝试子键
                                for sub in ("5.0", "7.0", "8.0"):
                                    try:
                                        with winreg.OpenKey(ver_key, sub) as sk:
                                            install_dir, _ = winreg.QueryValueEx(sk, "InstallPath")
                                            break
                                    except OSError:
                                        continue
                            if install_dir:
                                found.append((major, install_dir.rstrip("\\")))
                    except OSError:
                        continue
        except OSError:
            continue
    # 去重并按版本降序
    unique: dict[int, str] = {}
    for ver, path in found:
        if ver not in unique:
            unique[ver] = path
    return sorted(unique.items(), key=lambda x: -x[0])


# ---------------------------------------------------------------------------
# VARIANT marshalling 辅助函数
# 语义来自 Rhino-Link 技能文档第 3、4.2 节
# ---------------------------------------------------------------------------


def to_nested_variant_r8(*args: Any) -> Any:
    """嵌套浮点数组 VARIANT：Array(Array(x,y,z), ...) → SAFEARRAY(SAFEARRAY(R8))。"""
    import pythoncom
    return pythoncom.MakeVariant(_flatten_nested(args, float))


def to_nested_variant_i4(*args: Any) -> Any:
    """嵌套整数数组 VARIANT：Array(Array(i0,i1,...), ...)。"""
    import pythoncom
    return pythoncom.MakeVariant(_flatten_nested(args, int))


def to_flat_variant_r8(*args: Any) -> Any:
    """平铺浮点数组 VARIANT：Array(n1, n2, ...)。"""
    import pythoncom
    flat = []
    for a in args:
        if isinstance(a, (list, tuple)):
            flat.extend(float(x) for x in a)
        else:
            flat.append(float(a))
    return pythoncom.MakeVariant(flat)


def to_flat_variant_i4(*args: Any) -> Any:
    """平铺整数数组 VARIANT。"""
    import pythoncom
    flat = []
    for a in args:
        if isinstance(a, (list, tuple)):
            flat.extend(int(x) for x in a)
        else:
            flat.append(int(a))
    return pythoncom.MakeVariant(flat)


def rgb(r: int, g: int, b: int) -> int:
    """RGB(r,g,b) → 32-bit Long 颜色值。"""
    return (int(r) & 0xFF) | ((int(g) & 0xFF) << 8) | ((int(b) & 0xFF) << 16)


def _flatten_nested(args: tuple, caster: type) -> list:
    """把嵌套 list/tuple 转成 list[list]（双层），叶子用 caster 转换。

    支持两种调用形式（技能文档第 3 节）：
      to_nested_variant_r8([(0,0,0),(10,0,0)])   # 传一个列表
      to_nested_variant_r8((0,0,0),(10,0,0))     # 多参数变参
    两种都产出 [[0,0,0],[10,0,0]]。
    """
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        first = args[0]
        if len(first) > 0 and isinstance(first[0], (list, tuple)):
            rows = list(first)
        else:
            rows = [first]
    else:
        rows = list(args)
    return [[caster(x) for x in row] for row in rows]


# ---------------------------------------------------------------------------
# 主连接
# ---------------------------------------------------------------------------


def get_rhino() -> ConnectResult:
    if sys.platform != "win32":
        return ConnectResult(
            ok=False,
            software="Rhino",
            message=f"Rhino COM 只能在 Windows 上附着或启动 Rhino.exe。当前系统是 {sys.platform}。",
            evidence=EVIDENCE,
            entry="adapters.rhino_host.get_rhino",
        )

    try:
        import win32com.client
        import pythoncom
    except ImportError as exc:
        return ConnectResult(
            ok=False,
            software="Rhino",
            message=f"缺少 pywin32：{exc}。请 pip install pywin32。",
            evidence=EVIDENCE,
            entry="adapters.rhino_host.get_rhino",
        )

    pythoncom.CoInitialize()

    # 先尝试附着已运行实例。注意顺序：gencache.EnsureDispatch / Dispatch
    # 走的是 CoCreateInstance，会新建一个 Rhino 进程，不能当作“附着”用。
    rhino = None
    attached = False
    try:
        rhino = win32com.client.GetActiveObject("Rhino.Interface")
        attached = True
    except Exception:
        rhino = None

    if rhino is None:
        try:
            # 早期绑定——比 Dispatch 更接近官方 get_rhino，但会新建实例
            rhino = win32com.client.gencache.EnsureDispatch("Rhino.Interface")
        except Exception:
            try:
                rhino = win32com.client.Dispatch("Rhino.Interface")
            except Exception:
                rhino = None

    if rhino is None:
        # 没有运行实例，按注册表最高版本启动
        versions = _installed_rhino_versions()
        if not versions:
            return ConnectResult(
                ok=False,
                software="Rhino",
                message=(
                    "没有运行中的 Rhino，且注册表未找到已安装的 Rhino。"
                    "请先打开已授权的 Rhino。"
                ),
                evidence=EVIDENCE,
                entry="adapters.rhino_host.get_rhino",
            )
        top_ver, install_dir = versions[0]
        exe = os.path.join(install_dir, "System", "Rhino.exe")
        if not os.path.isfile(exe):
            exe = os.path.join(install_dir, "Rhino.exe")
        try:
            subprocess.Popen([exe], cwd=install_dir)
        except OSError as exc:
            return ConnectResult(
                ok=False,
                software="Rhino",
                message=f"启动 Rhino 失败：{exc}",
                evidence=EVIDENCE,
                entry="adapters.rhino_host.get_rhino",
            )
        # 等待 Rhino 起来（最长 30 秒）
        import time
        for _ in range(30):
            time.sleep(1)
            try:
                rhino = win32com.client.GetActiveObject("Rhino.Interface")
                break
            except Exception:
                continue
        if rhino is None:
            return ConnectResult(
                ok=False,
                software="Rhino",
                message="已启动 Rhino.exe，但 30 秒内 COM 接口仍不可用。请手动打开 Rhino 后重试。",
                evidence=EVIDENCE,
                entry="adapters.rhino_host.get_rhino",
            )

    try:
        script = rhino.GetScriptObject()
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software="Rhino",
            message=f"GetScriptObject 失败：{type(exc).__name__}: {exc}",
            evidence=EVIDENCE,
            entry="adapters.rhino_host.get_rhino",
        )

    # 探测版本
    version = 8
    try:
        ver_str = str(rhino.Version)
        for ch in ver_str:
            if ch.isdigit():
                version = int(ch)
                break
    except Exception:
        pass

    how = "已附着正在运行的 Rhino" if attached else "已新建并连接 Rhino（原实例不存在）"
    return ConnectResult(
        ok=True,
        software="Rhino",
        message=f"{how}（版本 {version}）。",
        evidence=EVIDENCE,
        entry="adapters.rhino_host.get_rhino",
        live_verified=True,
        injected=["rhino", "script"],
        details={
            "value": (rhino, script, version),
            "version": version,
            "helpers": {
                "to_nested_variant_r8": to_nested_variant_r8,
                "to_nested_variant_i4": to_nested_variant_i4,
                "to_flat_variant_r8": to_flat_variant_r8,
                "to_flat_variant_i4": to_flat_variant_i4,
                "rgb": rgb,
            },
        },
    )
