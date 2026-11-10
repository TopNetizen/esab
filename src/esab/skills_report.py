"""供诊断脚本调用：打印技能哈希核对，不打印授权信息。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from esab.skills import verify_installed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-home", required=True)
    args = parser.parse_args(argv)
    report = verify_installed(Path(args.agent_home))
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report["matched"] == report["expected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
