# -*- coding: utf-8 -*-
"""用同一 MCP 通道验证插件的 python_executor + COM 层（Excel），并验证会话持久化。"""
import asyncio
import sys
import traceback
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SKILLS_ROOT = r"D:\myagent\sab-040a1-test\src\esab\data\skills"

CODE_COM = r'''
import win32com.client as w32
probe = "SAB-PROBE-" + __import__("uuid").uuid4().hex[:8]
excel = w32.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
wb = excel.Workbooks.Add()
ws = wb.Worksheets(1)
ws.Range("A1").Value = probe
ws.Range("B1").Formula = "=2*3+4"
readback = ws.Range("A1").Value
formula_value = ws.Range("B1").Value
print("EXCEL_VERSION:", excel.Version)
print("WRITE_READBACK_MATCH:", readback == probe, "|", readback)
print("FORMULA_EVAL:", formula_value)
wb.Close(SaveChanges=False)
excel.Quit()
print("EXCEL_CLOSED_NO_SAVE")
_SAB_PERSIST = probe
'''

CODE_PERSIST = r'''
print("PERSIST_ACROSS_CALLS:", _SAB_PERSIST)
print("WORKSPACE_DIR:", WORKSPACE_DIR)
'''


async def main() -> int:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "esab", "agent", "--skills-root", SKILLS_ROOT],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=300.0) as session:
            await session.initialize()
            r1 = await session.call_tool("python_executor", {"code": CODE_COM, "timeout_seconds": 180})
            print("[COM] is_error =", r1.is_error)
            print(r1.content[0].text if r1.content else "")
            r2 = await session.call_tool("python_executor", {"code": CODE_PERSIST, "timeout_seconds": 60})
            print("[PERSIST] is_error =", r2.is_error)
            print(r2.content[0].text if r2.content else "")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
