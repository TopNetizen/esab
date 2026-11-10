"""CAD 产品 ProgID 兼容层。

pyautocad 0.2.0 在 ``Autocad.app`` 里硬编码 ``AutoCAD.Application``，
而且构造过程是惰性的（``_app`` 保持 ``None``，首次访问 ``.app`` 才连 COM）。
浩辰（GstarCAD/GCAD）、中望（ZWCAD）注册的是各自的产品 ProgID，
因此这里做两件事：

1. 解析当前可用的产品 ProgID（优先已运行的实例）；
2. 把 ``comtypes.client.GetActiveObject/CreateObject`` 对
   ``AutoCAD.Application`` 的请求重定向到解析出来的 ProgID，
   使 pyautocad 的既有 API（``acad.model.AddLine`` 等）可以原样使用。
"""

from __future__ import annotations

import sys

# 顺序即优先级：用户机器上同时存在多个产品时，先按当前运行的实例判断
CANDIDATE_PROGIDS: tuple[str, ...] = (
    "AutoCAD.Application",   # Autodesk AutoCAD
    "GstarCAD.Application",  # 浩辰 CAD
    "GCAD.Application",      # 浩辰 CAD（旧 ProgID）
    "ZWCAD.Application",     # 中望 CAD
    "BricscadApp.AcadApplication",
)

PRODUCT_NAMES = {
    "AutoCAD.Application": "AutoCAD",
    "GstarCAD.Application": "浩辰 CAD",
    "GCAD.Application": "浩辰 CAD",
    "ZWCAD.Application": "中望 CAD",
    "BricscadApp.AcadApplication": "BricsCAD",
}

_patched: str | None = None


def _require_windows() -> None:
    if sys.platform != "win32":
        raise RuntimeError(f"CAD 的 COM 连接需要 Windows，当前是 {sys.platform}")


def running_progid() -> str | None:
    """返回当前正在运行的可连接产品 ProgID；没有则 None。"""
    _require_windows()
    import comtypes.client as cc

    for progid in CANDIDATE_PROGIDS:
        try:
            cc.GetActiveObject(progid, dynamic=True)
            return progid
        except OSError:
            continue
        except Exception:
            continue
    return None


def _patch_comtypes(progid: str) -> None:
    """让 pyautocad 对 AutoCAD.Application 的请求落到实际产品 ProgID 上。"""
    global _patched
    if _patched == progid:
        return
    import comtypes.client as cc

    original_get = getattr(cc, "_sab_original_get_active_object", None) or cc.GetActiveObject
    original_create = getattr(cc, "_sab_original_create_object", None) or cc.CreateObject
    cc._sab_original_get_active_object = original_get
    cc._sab_original_create_object = original_create

    def get_active_object(p, *args, **kwargs):
        if str(p).strip().lower() == "autocad.application":
            p = progid
        return original_get(p, *args, **kwargs)

    def create_object(p, *args, **kwargs):
        if str(p).strip().lower() == "autocad.application":
            p = progid
        return original_create(p, *args, **kwargs)

    cc.GetActiveObject = get_active_object
    cc.CreateObject = create_object
    _patched = progid


def connect_cad(cad_type: str | None = None, visible: bool = True, create_if_not_exists: bool | None = None):
    """返回 ``(acad, info)``。

    ``acad`` 是 pyautocad 的 ``Autocad`` 实例，``acad.model`` / ``acad.app`` 可直接使用。
    ``info`` 是连接简报 dict，便于 print 出来留证据。

    连接会**真实触发**一次 COM 往返（读取 ``app.Version``），
    因此返回成功即代表确实连上了某个 CAD 实例，不会出现惰性构造造成的假成功。
    """
    _require_windows()

    if cad_type:
        requested = cad_type if "." in cad_type else f"{cad_type}.Application"
        matches = [p for p in CANDIDATE_PROGIDS if p.lower() == requested.lower()]
        if not matches:
            raise ValueError(f"不支持的 cad_type={cad_type!r}，可用：{', '.join(CANDIDATE_PROGIDS)}")
        progid = matches[0]
    else:
        progid = running_progid() or CANDIDATE_PROGIDS[0]

    if create_if_not_exists is None:
        create_if_not_exists = running_progid() is None

    _patch_comtypes(progid)

    from pyautocad import Autocad

    acad = Autocad(create_if_not_exists=create_if_not_exists, visible=visible)
    version = acad.app.Version  # 真正触发 COM，失败在这里抛出而不是延后

    info = {
        "progid": progid,
        "product": PRODUCT_NAMES.get(progid, progid),
        "version": version,
        "document": acad.app.ActiveDocument.Name,
        "created": bool(create_if_not_exists),
    }
    return acad, info
