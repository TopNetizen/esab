"""持久 Python 进程。从 stdin 接收一行 JSON，执行后回一行 JSON。"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from esab.runtime.builtins import execute, install
from esab.runtime.state import STATE


def main() -> None:
    try:
        import esab_shim  # noqa: F401
    except ImportError:
        pass
    agent_home = os.environ.get("ESAB_HOME", "")
    if agent_home:
        packages = Path(agent_home) / "resources" / "backend" / "local_packages"
        backend = Path(agent_home) / "resources" / "backend"
        for path in (backend, packages):
            if path.is_dir() and str(path) not in sys.path:
                sys.path.insert(0, str(path))
    STATE.skills_root = os.environ.get("ESAB_SKILLS_ROOT")
    STATE.agent_home = agent_home or None
    namespace: dict[str, object] = {"__name__": "__main__"}
    install(namespace)
    for line in sys.stdin:
        if not line.strip():
            continue
        message = json.loads(line)
        if message.get("op") != "exec":
            print(json.dumps({"ok": False, "stdout": "", "error": "未知操作"}), flush=True)
            continue
        result = execute(str(message.get("code") or ""), namespace)
        print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
