# -*- coding: utf-8 -*-
"""阶段C-2：修正读回对象（浩辰 Documents.Add 后 ActiveDocument 不会自动切换）。"""
import asyncio
import sys
import traceback

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SKILLS_ROOT = r"D:\myagent\sab-040a1-test\src\esab\data\skills"

CODE_DRAW = r'''
import pyautocad
from pyautocad import APoint

acad = connect_cad()
app = acad.app

docs_before = [(i, app.Documents.Item(i).Name) for i in range(app.Documents.Count)]
print("OPEN_DOCS:", docs_before)

doc = app.ActiveDocument
try:
    new_doc = app.Documents.Add()
    doc = new_doc
    try:
        doc.Activate()          # 浩辰需要显式激活，否则 ActiveDocument 还停在旧图
        print("ACTIVATE: ok")
    except Exception as exc:
        print("ACTIVATE: 不可用", type(exc).__name__, exc)
except Exception as exc:
    print("Documents.Add 失败，用当前图:", type(exc).__name__, exc)

print("TEST_DOC:", doc.Name, "| 新建后 ActiveDocument:", app.ActiveDocument.Name)

try:
    layer = doc.Layers.Add("SAB-TEST")
except Exception:
    layer = doc.Layers.Item("SAB-TEST")
layer.color = 6

ms = doc.ModelSpace
for obj in list(ms):
    try:
        if obj.Layer == "SAB-TEST":
            obj.Delete()
    except Exception:
        pass

before = ms.Count
line = ms.AddLine(APoint(0, 0, 0), APoint(6000, 0, 0)); line.Layer = "SAB-TEST"
circle = ms.AddCircle(APoint(3000, 1500, 0), 800); circle.Layer = "SAB-TEST"
pts = pyautocad.aDouble([0, 3000, 0, 6000, 3000, 0, 6000, 4500, 0, 0, 4500, 0])
pl = ms.AddPolyline(pts); pl.Closed = True; pl.Layer = "SAB-TEST"
txt = ms.AddText("浩辰CAD 插件测试 SAB 0.4.0a1", APoint(150, 7600, 0), 420); txt.Layer = "SAB-TEST"
dim = ms.AddDimAligned(APoint(0, 0, 0), APoint(6000, 0, 0), APoint(3000, -900, 0)); dim.Layer = "SAB-TEST"

after = ms.Count
print("ENTITY_DELTA:", before, "->", after, "| 新增", after - before)

SAB_ACAD = acad
SAB_DOC = doc
doc.Regen(1)
app.ZoomExtents()
print("STEP1 done, 测试图:", SAB_DOC.Name)
'''

CODE_VERIFY = r'''
print("SESSION_REUSE:", SAB_ACAD.app.Name, SAB_ACAD.app.Version)
doc = SAB_DOC
print("TEST_DOC_NOW:", doc.Name, "| ActiveDocument:", SAB_ACAD.app.ActiveDocument.Name)

found = {}
detail = []
for obj in list(doc.ModelSpace):
    try:
        if obj.Layer == "SAB-TEST":
            found[obj.EntityName] = found.get(obj.EntityName, 0) + 1
            if obj.EntityName == "AcDbCircle":
                detail.append(f"圆 圆心={tuple(round(v,2) for v in obj.Center)} 半径={round(obj.Radius,2)}")
            elif obj.EntityName == "AcDbText":
                detail.append(f"文字='{obj.TextString}' 高={round(obj.Height,1)}")
            elif obj.EntityName in ("AcDbLine", "AcDbPolyline"):
                detail.append(f"{obj.EntityName} 长度/周长={round(obj.Length,2)} 闭合={getattr(obj,'Closed','n/a')}")
            elif obj.EntityName == "AcDbAlignedDimension":
                detail.append(f"对齐标注 文字覆盖={getattr(obj,'TextOverride','')!r}")
    except Exception as exc:
        detail.append(f"读取异常 {type(exc).__name__}: {exc}")

print("图层 SAB-TEST 统计:", found)
for d in detail:
    print("  -", d)
print("EXTMIN:", tuple(round(v, 2) for v in doc.GetVariable("EXTMIN")))
print("EXTMAX:", tuple(round(v, 2) for v in doc.GetVariable("EXTMAX")))
print("STEP2 done")
'''


async def main() -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "esab", "agent", "--skills-root", SKILLS_ROOT],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=300.0) as session:
            await session.initialize()
            r1 = await session.call_tool("python_executor", {"code": CODE_DRAW, "timeout_seconds": 180})
            print("[1] 绘图 is_error =", r1.is_error)
            print(r1.content[0].text if r1.content else "")
            r2 = await session.call_tool("python_executor", {"code": CODE_VERIFY, "timeout_seconds": 120})
            print("[2] 读回 is_error =", r2.is_error)
            print(r2.content[0].text if r2.content else "")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
