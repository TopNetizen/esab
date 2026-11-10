"""新适配器模块的离线单测（不依赖真实工程软件）。"""

from __future__ import annotations

import sys


def test_rhino_nested_variant_shape():
    """to_nested_variant_r8/i4 必须产出双层 list，不是三层。"""
    from esab.adapters.rhino_host import _flatten_nested

    # 形式 1：传一个 list of points
    out = _flatten_nested(([(0, 0, 0), (10, 0, 0)],), float)
    assert out == [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]], out

    # 形式 2：变参，每个 point 一个参数
    out = _flatten_nested(((0, 0, 0), (10, 0, 0)), float)
    assert out == [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]], out

    # 单点也要包成一行
    out = _flatten_nested(([1, 2, 3],), int)
    assert out == [[1, 2, 3]], out


def test_staad_discovery_returns_empty_on_non_windows(monkeypatch):
    """非 Windows 或无 STAAD 安装时，ensure_openstaadpy_installed 返回诊断而不是崩溃。"""
    from esab.adapters import staad_discovery

    monkeypatch.setattr(sys, "platform", "linux")
    installs = staad_discovery.find_staad_installs()
    assert installs == []


def test_tekla_vendored_module_importable():
    """vendored tekla 包可 import（不真的连 Tekla）。"""
    from esab.adapters.tekla import detect, runtime  # noqa: F401

    assert hasattr(runtime, "connect_tekla")
    assert hasattr(detect, "detect")


def test_vendor_shim_rhino_exports_helpers():
    """vendor_shim 必须导出 5 个 VARIANT 辅助函数，技能脚本才能 import。"""
    from esab_shim.software_link_kit import rhino as shim

    for name in (
        "get_rhino",
        "to_nested_variant_r8",
        "to_nested_variant_i4",
        "to_flat_variant_r8",
        "to_flat_variant_i4",
        "rgb",
    ):
        assert hasattr(shim, name), f"vendor_shim.rhino 缺少 {name}"
