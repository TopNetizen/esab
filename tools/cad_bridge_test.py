# -*- coding: utf-8 -*-
"""端到端测试：以 MCP 客户端身份启动 esab agent，操作本机 AutoCAD。"""
import asyncio
import json
import sys
import traceback
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SKILLS_ROOT = r"D:\myagent\sab-040a1-test\src\esab\data\skills"

CODE_CONNECT_DRAW = r'''
import math, time
import pyautocad
from pyautocad import Autocad, APoint

acad = Autocad(create_if_not_exists=True, visible=True)
print("STEP1 connected")
print("APP_VERSION:", acad.app.Version)
print("APP_CAPTION:", acad.app.Caption)

doc = acad.app.ActiveDocument
print("ACTIVE_DOC:", doc.Name)

# 保护用户图纸：若当前不是空白 Drawing1，则新建空白图纸再画
if "Drawing1.dwg" not in doc.Name:
    doc = acad.app.Documents.Add()
    print("NEW_DOC_FOR_TEST:", doc.Name)

try:
    layer = doc.Layers.Add("SAB-TEST")
except Exception:
    layer = doc.Layers.Item("SAB-TEST")
layer.color = 1

ms = doc.ModelSpace

# 清掉上次测试遗留的同名测试图元，避免重复堆积
for obj in list(ms):
    try:
        if obj.Layer == "SAB-TEST":
            obj.Delete()
    except Exception:
        pass

before = ms.Count

line = ms.AddLine(APoint(0, 0, 0), APoint(6000, 0, 0))
line.Layer = "SAB-TEST"

circle = ms.AddCircle(APoint(3000, 1500, 0), 800)
circle.Layer = "SAB-TEST"

pts = pyautocad.aDouble([0, 3000, 0, 6000, 3000, 0, 6000, 4500, 0, 0, 4500, 0])
pl = ms.AddPolyline(pts)
pl.Closed = True
pl.Layer = "SAB-TEST"

txt = ms.AddText("SAB 0.4.0a1 CAD 插件测试", APoint(150, 7600, 0), 420)
txt.Layer = "SAB-TEST"

dim = ms.AddDimAligned(APoint(0, 0, 0), APoint(6000, 0, 0), APoint(3000, -900, 0))
dim.Layer = "SAB-TEST"

after = ms.Count
print("ENTITY_COUNT:", before, "->", after, "新增", after - before)

acad.app.ZoomExtents()
print("STEP1 done")
'''

CODE_VERIFY = r'''
# 同一个 python 进程内 acad 应仍然有效（会话持久的窗口，验证是否会重复启动 CAD）
import pyautocad
from pyautocad import APoint

print("REUSED_ACAD:", acad.app.Version, "| doc:", acad.app.ActiveDocument.Name)

doc = acad.app.ActiveDocument
found = []
for obj in list(doc.ModelSpace):
    try:
        if obj.Layer == "SAB-TEST":
            found.append(obj.EntityName)
    except Exception:
        pass
print("SAB-TEST 图层图元:", found)

for obj in doc.ModelSpace:
    if obj.EntityName == "AcDbCircle":
        try:
            if abs(obj.Center[0] - 3000) < 1 and abs(obj.Center[1] - 1500) < 1:
                print("圆检验: 圆心", obj.Center, "半径", obj.Radius)
        except Exception:
            pass

for t in doc.ModelSpace:
    if t.EntityName == "AcDbText" and t.Layer == "SAB-TEST":
        print("文字检验:", t.TextString, "位置", t.InsertionPoint)

print("EXTMIN/EXTMAX:", doc.GetVariable("EXTMIN"), doc.GetVariable("EXTMAX"))
print("STEP2 done")
'''


async def main() -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "esab", "agent", "--skills-root", SKILLS_ROOT],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=600.0) as session:
            init = await session.initialize()
            print("[1] initialize OK ->", init.server_info.name, init.server_info.version)

            tools = await session.list_tools()
            print("[2] tools:", [t.name for t in tools.tools])

            res = await session.call_tool("list_software_adapters", {})
            data = json.loads(res.content[0].text)
            cad = [a for a in data["adapters"] if a.get("software") == "CAD"]
            print("[3] CAD adapter:", json.dumps(cad, ensure_ascii=False))

            r = await session.call_tool("use_skill", {"name": "AutoCAD-Link"})
            text = r.content[0].text if r.content else ""
            print("[4] use_skill AutoCAD-Link len =", len(text), "| is_error =", r.is_error)
            print("    skill head:", text[:120].replace("\n", " "))

            print("[5] python_executor #1 (连接并绘图) ... 启动 AutoCAD 可能要 1-2 分钟")
            r1 = await session.call_tool("python_executor", {"code": CODE_CONNECT_DRAW, "timeout_seconds": 300})
            print("    is_error =", r1.is_error)
            print(r1.content[0].text if r1.content else "")

            print("[6] python_executor #2 (同会话读回验证)")
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
