# -*- coding: utf-8 -*-
"""阶段C：走插件 MCP 通道，对浩辰CAD 做真实绘图与读回测试。"""
import asyncio
import json
import sys
import traceback

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SKILLS_ROOT = r"D:\myagent\sab-040a1-test\src\esab\data\skills"

CODE_CONNECT_DRAW = r'''
import math
import pyautocad
from pyautocad import APoint

acad = connect_cad()          # 运行时注入：自动解析 AutoCAD / 浩辰 / 中望
print("PROGID_CHECK:", acad.app.Name, acad.app.Version)

app = acad.app
doc = app.ActiveDocument
print("ACTIVE_DOC_BEFORE:", doc.Name)

# 不用用户正在编辑的图纸：新建一张测试图
try:
    test_doc = app.Documents.Add()
    doc = test_doc
    print("NEW_DOC:", doc.Name)
except Exception as exc:
    print("Documents.Add 不可用，改用当前图纸:", type(exc).__name__, exc)

try:
    layer = doc.Layers.Add("SAB-TEST")
except Exception:
    layer = doc.Layers.Item("SAB-TEST")
layer.color = 1

ms = doc.ModelSpace
before = ms.Count

line = ms.AddLine(APoint(0, 0, 0), APoint(6000, 0, 0))
line.Layer = "SAB-TEST"

circle = ms.AddCircle(APoint(3000, 1500, 0), 800)
circle.Layer = "SAB-TEST"

pts = pyautocad.aDouble([0, 3000, 0, 6000, 3000, 0, 6000, 4500, 0, 0, 4500, 0])
pl = ms.AddPolyline(pts)
pl.Closed = True
pl.Layer = "SAB-TEST"

txt = ms.AddText("浩辰CAD 插件测试 SAB 0.4.0a1", APoint(150, 7600, 0), 420)
txt.Layer = "SAB-TEST"

dim = ms.AddDimAligned(APoint(0, 0, 0), APoint(6000, 0, 0), APoint(3000, -900, 0))
dim.Layer = "SAB-TEST"

after = ms.Count
print("ENTITY_DELTA:", before, "->", after, "| 新增", after - before)

doc.Regen(1)
app.ZoomExtents()
print("STEP1 done")
'''

CODE_VERIFY = r'''
import pyautocad
from pyautocad import APoint

print("REUSED_SESSION:", acad.app.Name, acad.app.Version, "| doc:", acad.app.ActiveDocument.Name)
doc = acad.app.ActiveDocument

found = {}
for obj in list(doc.ModelSpace):
    try:
        if obj.Layer == "SAB-TEST":
            found[obj.EntityName] = found.get(obj.EntityName, 0) + 1
    except Exception:
        pass
print("图层 SAB-TEST 图元统计:", found)

for obj in list(doc.ModelSpace):
    if obj.EntityName == "AcDbCircle" and getattr(obj, "Layer", "") == "SAB-TEST":
        print("圆: 圆心", tuple(round(v, 2) for v in obj.Center), "半径", round(obj.Radius, 2))
    if obj.EntityName == "AcDbText" and getattr(obj, "Layer", "") == "SAB-TEST":
        print("文字:", obj.TextString)
    if obj.EntityName in ("AcDbLine", "AcDbPolyline") and getattr(obj, "Layer", "") == "SAB-TEST":
        try:
            print(obj.EntityName, "长度/周长:", round(obj.Length, 2))
        except Exception:
            pass

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

            res = await session.call_tool("list_software_adapters", {})
            cad = [a for a in json.loads(res.content[0].text)["adapters"] if a.get("software") == "CAD"]
            print("[1] CAD adapter entry:", cad[0]["entry"], "| evidence:", cad[0]["evidence"])

            r = await session.call_tool("use_skill", {"name": "AutoCAD-Link"})
            print("[2] use_skill len =", len(r.content[0].text), "| is_error =", r.is_error)

            print("[3] python_executor #1 连接 + 绘图")
            r1 = await session.call_tool("python_executor", {"code": CODE_CONNECT_DRAW, "timeout_seconds": 180})
            print("    is_error =", r1.is_error)
            print(r1.content[0].text if r1.content else "")

            print("[4] python_executor #2 读回验证")
            r2 = await session.call_tool("python_executor", {"code": CODE_VERIFY, "timeout_seconds": 120})
            print("    is_error =", r2.is_error)
            print(r2.content[0].text if r2.content else "")
    print("ALL STEPS DONE")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
