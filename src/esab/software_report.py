"""打印 15 类软件的连接诊断。不调用建模或计算。"""

from __future__ import annotations

import json

from esab.adapters.hosts import (
    CATALOG,
    connect_abaqus,
    connect_bimbase,
    connect_cad,
    connect_etabs,
    connect_gbp,
    connect_midas,
    connect_plants,
    connect_rhino,
    connect_sap2000,
    connect_sausg,
    connect_sketchup,
    connect_staad,
    connect_structural_cae,
    connect_structural_pm,
    connect_tekla,
)

PROBES = {
    "PKPM": connect_structural_pm,
    "SAP2000": connect_sap2000,
    "ETABS": connect_etabs,
    "STAAD": connect_staad,
    "MIDAS GEN NX": connect_midas,
    "PKPM-CAE": connect_structural_cae,
    "Abaqus": connect_abaqus,
    "Tekla": connect_tekla,
    "SAUSG": connect_sausg,
    "Rhino": connect_rhino,
    "CAD": connect_cad,
    "SketchUp": connect_sketchup,
    "BIMBase": connect_bimbase,
    "PlantS": connect_plants,
    "GBP": connect_gbp,
}


def main() -> int:
    rows = []
    evidence = {item["software"]: item for item in CATALOG}
    for software, probe in PROBES.items():
        result = probe()
        item = evidence[software]
        rows.append(
            {
                "software": software,
                "entry": item["entry"],
                "evidence": item["evidence"],
                "ok": result.ok,
                "live_verified": result.live_verified,
                "message": result.message,
            }
        )
    print(json.dumps({"probes": rows, "writes_performed": False}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
