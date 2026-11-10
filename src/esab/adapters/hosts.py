"""用户列出的 15 类软件的连接入口。

连接代码只使用技能正文或 software_link_kit 字符串里出现过的符号。
本机没有该软件时返回诊断，不报告成功。
"""

from __future__ import annotations

import os
import sys
from typing import Any

from esab.adapters.common import ConnectResult
from esab.adapters.mcp_upstream import connect_streamable, url_from_env
from esab.adapters.port_discovery import discover_mcp_url

CATALOG: list[dict[str, str]] = [
    {
        "software": "PKPM",
        "server_name": "pkpmmcp",
        "kind": "mcp",
        "env": "STRUCT_MCP_URL",
        "evidence": "MCP 端口自动发现，地址形如 http://127.0.0.1:{port}/mcp",
        "entry": "adapters.hosts.connect_structural_pm",
    },
    {
        "software": "SAP2000",
        "server_name": "",
        "kind": "com",
        "env": "",
        "evidence": "SAP2000-Link：SAP2000v1.Helper 与 CSI.SAP2000.API.SapObject",
        "entry": "adapters.hosts.connect_sap2000",
    },
    {
        "software": "ETABS",
        "server_name": "",
        "kind": "com",
        "env": "",
        "evidence": "ETABS-Link：ETABSv1.Helper 与 CSI.ETABS.API.ETABSObject",
        "entry": "adapters.hosts.connect_etabs",
    },
    {
        "software": "STAAD",
        "server_name": "",
        "kind": "com",
        "env": "",
        "evidence": "STAADPro-Link：openstaadpy.os_analytical.connect()，只挂已打开的模型",
        "entry": "adapters.hosts.connect_staad",
    },
    {
        "software": "MIDAS GEN NX",
        "server_name": "",
        "kind": "rest",
        "env": "MIDAS_BASE_URL",
        "evidence": "software_link_kit/midas.py：connect_midas()、MidasClient、MAPI-Key、/db/NODE",
        "entry": "adapters.hosts.connect_midas",
    },
    {
        "software": "PKPM-CAE",
        "server_name": "cae-mcp",
        "kind": "mcp",
        "env": "STRUCT_CAE_MCP_URL",
        "evidence": "手册与注册表 id cae-mcp。固定端口未公开",
        "entry": "adapters.hosts.connect_structural_cae",
    },
    {
        "software": "Abaqus",
        "server_name": "",
        "kind": "official-module",
        "env": "",
        "evidence": "通过 TCP 连接 Abaqus CAE 加载的桥接插件",
        "entry": "adapters.hosts.connect_abaqus",
    },
    {
        "software": "Tekla",
        "server_name": "",
        "kind": "official-module",
        "env": "",
        "evidence": "通过 pythonnet 连接已运行的 Tekla Structures 实例",
        "entry": "adapters.hosts.connect_tekla",
    },
    {
        "software": "SAUSG",
        "server_name": "ssgmcp",
        "kind": "mcp",
        "env": "SAUSG_MCP_URL",
        "evidence": "SSG-Link：connect_to_server('ssgmcp')，cmd_args 例为 -sausage",
        "entry": "adapters.hosts.connect_sausg",
    },
    {
        "software": "Rhino",
        "server_name": "",
        "kind": "official-module",
        "env": "",
        "evidence": "通过 COM 连接已运行的 Rhino 实例",
        "entry": "adapters.hosts.connect_rhino",
    },
    {
        "software": "CAD",
        "server_name": "",
        "kind": "com",
        "env": "",
        "evidence": "AutoCAD-Link：pyautocad.Autocad(create_if_not_exists, visible)",
        "entry": "adapters.hosts.connect_cad",
    },
    {
        "software": "SketchUp",
        "server_name": "",
        "kind": "official-module",
        "env": "",
        "evidence": "通过 TCP 连接 SketchUp 加载的 Ruby 桥接插件",
        "entry": "adapters.hosts.connect_sketchup",
    },
    {
        "software": "BIMBase",
        "server_name": "BIMBaseAI2PY_MCPServer",
        "kind": "mcp",
        "env": "BIMBASE_MCP_URL",
        "evidence": "注册表服务名 BIMBaseAI2PY_MCPServer。安装包里的远程地址含凭据，本工具不内置",
        "entry": "adapters.hosts.connect_bimbase",
    },
    {
        "software": "PlantS",
        "server_name": "plantsmcp",
        "kind": "mcp",
        "env": "PLANTS_MCP_URL",
        "evidence": "PlantS-Link：connect_to_plants()，不要把 connect_to_server 当首选",
        "entry": "adapters.hosts.connect_plants",
    },
    {
        "software": "GBP",
        "server_name": "gbpmcp",
        "kind": "mcp",
        "env": "GBP_MCP_URL",
        "evidence": "GBP-Link：gbpmcp.galp_tool_invoke，默认 URL http://127.0.0.1:3333/GBPBECA3/galpserver/mcp",
        "entry": "adapters.hosts.connect_gbp",
    },
]


def _discover_or_env(server_name: str, env_name: str, software: str, evidence: str) -> ConnectResult:
    """先读环境变量 URL，没有则自动发现端口。"""
    env_url = url_from_env(env_name)
    result = discover_mcp_url(server_name, env_url=env_url)
    if result.url is None:
        return ConnectResult(
            ok=False,
            software=software,
            server_name=server_name,
            message=result.error or "无法发现 MCP 地址。",
            evidence=evidence,
            entry="adapters.port_discovery.discover_mcp_url",
        )
    return connect_streamable(server_name, result.url, software, evidence)


def connect_structural_pm(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _discover_or_env(
        "pkpmmcp", "STRUCT_MCP_URL", "PKPM",
        "MCP 端口自动发现",
    )


def connect_structural_cae(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _discover_or_env(
        "cae-mcp", "STRUCT_CAE_MCP_URL", "PKPM-CAE",
        "MCP 端口自动发现",
    )


def connect_sausg(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _discover_or_env(
        "ssgmcp", "SAUSG_MCP_URL", "SAUSG",
        "SSG-Link：connect_to_server('ssgmcp')，端口自动发现",
    )


def connect_gbp(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _discover_or_env(
        "gbpmcp", "GBP_MCP_URL", "GBP",
        "GBP-Link：固定端口 3333/GBPBECA3/galpserver/mcp",
    )


def connect_plants(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _discover_or_env(
        "plantsmcp", "PLANTS_MCP_URL", "PlantS",
        "PlantS-Link：connect_to_plants()，端口自动发现",
    )


def connect_bimbase(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _discover_or_env(
        "BIMBaseAI2PY_MCPServer", "BIMBASE_MCP_URL", "BIMBase",
        "BIMBase-Link：端口自动发现，不内置安装包远程凭据",
    )


def connect_sap2000(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _connect_csi(
        software="SAP2000",
        helper_progid="SAP2000v1.Helper",
        helper_module="SAP2000v1.cHelper",
        object_name="CSI.SAP2000.API.SapObject",
        evidence="SAP2000-Link 连接片段",
    )


def connect_etabs(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    return _connect_csi(
        software="ETABS",
        helper_progid="ETABSv1.Helper",
        helper_module="ETABSv1.cHelper",
        object_name="CSI.ETABS.API.ETABSObject",
        evidence="ETABS-Link 连接片段",
    )


def _connect_csi(software: str, helper_progid: str, helper_module: str, object_name: str, evidence: str) -> ConnectResult:
    entry = "adapters.hosts._connect_csi"
    if sys.platform != "win32":
        return ConnectResult(
            ok=False,
            software=software,
            message=f"{software} 的 COM 连接只能在 Windows 上附着已经打开的实例。当前系统是 {sys.platform}。",
            evidence=evidence,
            entry=entry,
            details={"helper": helper_progid, "object": object_name},
        )
    try:
        import comtypes.client
    except ImportError as exc:
        return ConnectResult(
            ok=False,
            software=software,
            message=f"缺少 comtypes：{exc}。技能要求 comtypes.client.CreateObject({helper_progid!r})。",
            evidence=evidence,
            entry=entry,
            details={"helper": helper_progid, "object": object_name},
        )
    try:
        comtypes.CoInitialize()
        helper = comtypes.client.CreateObject(helper_progid)
        module_name, class_name = helper_module.split(".")
        generated = __import__(f"comtypes.gen.{module_name}", fromlist=[class_name])
        helper = helper.QueryInterface(getattr(generated, class_name))
        application = helper.GetObject(object_name)
        if application is None:
            return ConnectResult(
                ok=False,
                software=software,
                message=f"GetObject({object_name!r}) 返回 None。请先打开已授权的 {software} 和模型。本工具不会启动新实例。",
                evidence=evidence,
                entry=entry,
            )
        return ConnectResult(
            ok=True,
            software=software,
            message=f"已附着正在运行的 {software}。",
            evidence=evidence,
            entry=entry,
            live_verified=True,
            injected=["SapModel"],
            details={"application": application, "SapModel": application.SapModel},
        )
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software=software,
            message=f"{type(exc).__name__}: {exc}",
            evidence=evidence,
            entry=entry,
            details={"helper": helper_progid, "object": object_name},
        )


def connect_staad(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    evidence = "STAADPro-Link：openstaadpy.os_analytical.connect()（Bentley 官方开源库）"
    from esab.adapters.staad_discovery import ensure_openstaadpy_installed

    ok, install_msg = ensure_openstaadpy_installed()
    if not ok:
        return ConnectResult(
            ok=False,
            software="STAAD",
            message=install_msg,
            evidence=evidence,
            entry="adapters.staad_discovery.ensure_openstaadpy_installed",
        )
    try:
        from openstaadpy import os_analytical
    except ImportError as exc:
        return ConnectResult(
            ok=False,
            software="STAAD",
            message=f"openstaadpy 安装后仍无法 import：{exc}",
            evidence=evidence,
            entry="adapters.hosts.connect_staad",
        )
    try:
        session = os_analytical.connect()
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software="STAAD",
            message=f"{type(exc).__name__}: {exc}。请确认 STAAD.Pro 2025+ 已运行且打开了模型。",
            evidence=evidence,
            entry="adapters.hosts.connect_staad",
        )
    return ConnectResult(
        ok=True,
        software="STAAD",
        message=f"已挂接正在运行的 STAAD.Pro（{install_msg}）。",
        evidence=evidence,
        entry="adapters.hosts.connect_staad",
        live_verified=True,
        injected=["staad"],
        details={"session": session},
    )


def connect_midas(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    from esab.adapters.midas import connect_midas as _connect

    return _connect()


def connect_cad(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    evidence = "AutoCAD-Link：pyautocad.Autocad + ProgID 兼容层（AutoCAD / 浩辰 / 中望）"
    if sys.platform != "win32":
        return ConnectResult(
            ok=False,
            software="CAD",
            message=f"AutoCAD、浩辰 CAD、中望 CAD 的 pyautocad 连接需要 Windows。当前系统是 {sys.platform}。",
            evidence=evidence,
            entry="adapters.hosts.connect_cad",
        )
    try:
        from esab_shim.cad import connect_cad as _connect
    except ImportError as exc:
        return ConnectResult(
            ok=False,
            software="CAD",
            message=f"缺少 pyautocad 兼容层：{exc}。请 pip install esab[win32]。",
            evidence=evidence,
            entry="adapters.hosts.connect_cad",
        )
    try:
        # 默认只连已运行的实例；shim 内部会用 app.Version 做一次真实 COM 往返，
        # 因此这里的 ok 不会再是惰性构造造成的假成功。
        acad, info = _connect()
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software="CAD",
            message=f"{type(exc).__name__}: {exc}",
            evidence=evidence,
            entry="adapters.hosts.connect_cad",
        )
    return ConnectResult(
        ok=True,
        software="CAD",
        message=f"已连接 {info['product']} {info['version']}：{info['document']}（{info['progid']}）",
        evidence=evidence,
        entry="adapters.hosts.connect_cad",
        live_verified=True,
        injected=["acad"],
        details={"acad": acad, "cad_info": info},
    )


def _official_missing(software: str, evidence: str, module_path: str, function_name: str, detail: str) -> ConnectResult:
    return ConnectResult(
        ok=False,
        software=software,
        message=(
            f"官方连接模块不可用：{module_path}.{function_name}（{detail}）。"
            "该实现在桥接器的 Windows 扩展里，本环境没有把它反编译成另一套协议。"
            "在 Windows 上桥接层独立运行。"
        ),
        evidence=evidence,
        entry=f"{module_path}.{function_name}",
    )


def connect_official(module_path: str, function_name: str, software: str, evidence: str, **kwargs: Any) -> ConnectResult:
    try:
        module = __import__(module_path, fromlist=[function_name])
    except ImportError as exc:
        return _official_missing(software, evidence, module_path, function_name, str(exc))
    module_file = str(getattr(module, "__file__", "") or "").replace("\\", "/")
    if "vendor_shim" in module_file:
        return _official_missing(software, evidence, module_path, function_name, "当前只有兼容占位，不是官方 .pyd")
    function = getattr(module, function_name)
    try:
        value = function(**kwargs) if kwargs else function()
    except Exception as exc:
        return ConnectResult(
            ok=False,
            software=software,
            message=f"{type(exc).__name__}: {exc}",
            evidence=evidence,
            entry=f"{module_path}.{function_name}",
        )
    # 官方包装常见约定：失败时返回错误字符串而不是抛异常。
    # 不判这一条就会把“❌ 未找到已安装的 X”当成连接成功。
    if isinstance(value, str):
        return ConnectResult(
            ok=False,
            software=software,
            message=f"官方连接函数返回字符串（失败信号）：{value}",
            evidence=evidence,
            entry=f"{module_path}.{function_name}",
        )
    return ConnectResult(
        ok=True,
        software=software,
        message=f"{software} 官方连接函数已返回。",
        evidence=evidence,
        entry=f"{module_path}.{function_name}",
        live_verified=True,
        details={"value": value},
    )


def connect_abaqus(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del cmd_args
    from esab.adapters.abaqus_client import connect_abaqus as _connect

    return _connect(work_dir or os.getcwd())


def connect_tekla(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    from esab.adapters.tekla_host import connect_tekla as _connect

    return _connect()


def connect_rhino(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del work_dir, cmd_args
    from esab.adapters.rhino_host import get_rhino

    return get_rhino()


def connect_sketchup(work_dir: str | None = None, cmd_args: str | None = None) -> ConnectResult:
    del cmd_args
    from esab.adapters.sketchup_client import connect_sketchup as _connect
    return _connect(path=work_dir)


CONNECTORS = {
    "pkpmmcp": connect_structural_pm,
    "cae-mcp": connect_structural_cae,
    "ssgmcp": connect_sausg,
    "gbpmcp": connect_gbp,
    "plantsmcp": connect_plants,
    "BIMBaseAI2PY_MCPServer": connect_bimbase,
    "sap2000": connect_sap2000,
    "etabs": connect_etabs,
    "staad": connect_staad,
    "midas": connect_midas,
    "abaqus": connect_abaqus,
    "tekla": connect_tekla,
    "rhino": connect_rhino,
    "cad": connect_cad,
    "sketchup": connect_sketchup,
}
