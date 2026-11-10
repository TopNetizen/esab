# -*- coding: utf-8 -*-
"""阶段B：直接用浩辰自己的 ProgID 验证 COM/ActiveX 接口是否完整。"""
import sys
import win32com.client as w32

PROGIDS = ["GstarCAD.Application", "GCAD.Application"]

app = None
used = None
for p in PROGIDS:
    try:
        app = w32.GetActiveObject(p)
        used = p
        break
    except Exception as exc:
        print(f"GetActiveObject({p}) 失败: {type(exc).__name__}: {exc}")

print("USED_PROGID:", used)
if app is None:
    sys.exit(1)

print("VERSION:", app.Version)
print("NAME:", app.Name)
doc = app.ActiveDocument
print("ACTIVE_DOC:", doc.Name, "| 已有图元:", doc.ModelSpace.Count)
try:
    print("APP_CAPTION:", app.Caption)
except Exception as e:
    print("Caption 不可用:", e)
try:
    print("ZOOMEXTENTS 可用:", hasattr(app, "ZoomExtents"))
except Exception:
    pass
doc.Close(SaveChanges=False) if False else None
