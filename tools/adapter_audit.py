# -*- coding: utf-8 -*-
"""全量审计：逐个调用所有软件连接入口，记录是否在软件缺失时假报成功。"""
import json
import subprocess
import sys
import textwrap

ENTRIES = [
    ("PKPM", "connect_structural_pm", ""),
    ("PKPM-CAE", "connect_structural_cae", ""),
    ("SAUSG", "connect_sausg", ""),
    ("GBP", "connect_gbp", ""),
    ("PlantS", "connect_plants", ""),
    ("BIMBase", "connect_bimbase", ""),
    ("SAP2000", "connect_sap2000", ""),
    ("ETABS", "connect_etabs", ""),
    ("STAAD", "connect_staad", ""),
    ("MIDAS", "connect_midas", ""),
    ("Abaqus", "connect_abaqus", "D:/myagent/sab-040a1-test"),
    ("Tekla", "connect_tekla", ""),
    ("Rhino", "connect_rhino", ""),
    ("CAD", "connect_cad", ""),
    ("SketchUp", "connect_sketchup", ""),
]

CODE = textwrap.dedent(
    """
    import json, sys
    from esab.adapters import hosts
    fn = getattr(hosts, {name!r})
    try:
        r = fn({arg})
        print(json.dumps({{
            "ok": bool(r.ok),
            "software": r.software,
            "live_verified": bool(getattr(r, "live_verified", False)),
            "injected": list(getattr(r, "injected", []) or []),
            "message": str(r.message)[:300],
            "entry": r.entry,
        }}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({{"ok": "EXCEPTION", "message": f"{{type(exc).__name__}}: {{exc}}"}}, ensure_ascii=False))
    """
)

rows = []
for label, fn_name, arg in ENTRIES:
    code = CODE.format(name=fn_name, arg=repr(arg) if arg else "")
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=45,
            cwd=r"D:\myagent\sab-040a1-test",
        )
        out = (proc.stdout or "").strip().splitlines()
        data = json.loads(out[-1]) if out else {"ok": "NO_OUTPUT", "message": (proc.stderr or "")[-300:]}
    except subprocess.TimeoutExpired:
        data = {"ok": "TIMEOUT", "message": "45s 内未返回，疑似阻塞"}
    data["label"] = label
    data["entry_fn"] = fn_name
    rows.append(data)
    print(f"{label:10s} ok={data.get('ok')} live={data.get('live_verified')} :: {data.get('message','')[:140]}")

print("\n=== 统计 ===")
false_ok = [r for r in rows if r.get("ok") is True]
print("返回 ok=True 的：", [r["label"] for r in false_ok])
print("返回失败/异常的：", [r["label"] for r in rows if r.get("ok") is not True])

with open(r"D:\myagent\sab-040a1-test\adapter_audit.json", "w", encoding="utf-8") as fh:
    json.dump(rows, fh, ensure_ascii=False, indent=2)
