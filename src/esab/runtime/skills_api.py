"""读取随包分发的明文技能文件。不改写正文。"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from esab.runtime.state import STATE

_PKG_DATA = Path(__file__).resolve().parent.parent / "data"
_BUILTIN_SKILLS = _PKG_DATA / "skills"


def skills_root() -> Path | None:
    """优先用环境变量指定的目录；否则用包内自带的明文技能。"""
    raw = STATE.skills_root or os.environ.get("ESAB_SKILLS_ROOT", "")
    if raw:
        path = Path(raw)
        if path.is_dir():
            return path
    if _BUILTIN_SKILLS.is_dir():
        return _BUILTIN_SKILLS
    return None


def db_path(skill_name: str) -> Path | None:
    """返回包内随包分发的 SQLite 数据库路径。"""
    candidates = list((_PKG_DATA / "db").rglob("*.db"))
    for c in candidates:
        if skill_name.lower().replace("-", "") in c.stem.lower().replace("_", "").replace("-", ""):
            return c
    return None


def iter_skill_files():
    root = skills_root()
    if root is None:
        return
    for path in sorted(root.rglob("SKILL.md")):
        yield path


def skill_name(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        block = text[3:end] if end > 0 else ""
        for line in block.splitlines():
            if line.startswith("name:"):
                return line.split(":", 1)[1].strip().strip("\"'")
    return path.parent.name


def find_skill(name: str) -> Path | None:
    wanted = name.strip().lower()
    for path in iter_skill_files() or []:
        if skill_name(path).lower() == wanted or path.parent.name.lower() == wanted:
            return path
    return None


def use_skill(name: str, file: str | None = None, run: str | None = None, run_args: str = "") -> str:
    path = find_skill(name)
    if path is None:
        root = skills_root()
        return f"没有找到技能 {name}。技能目录：{root}"
    if file:
        target = (path.parent / file).resolve()
        if path.parent.resolve() not in target.parents and target != path.parent.resolve():
            return "拒绝读取技能目录之外的文件"
        if not target.is_file():
            return f"技能文件不存在：{file}"
        return target.read_text(encoding="utf-8")
    if run:
        script = (path.parent / run).resolve()
        if path.parent.resolve() not in script.parents and script != path.parent.resolve():
            return "拒绝执行技能目录之外的脚本"
        if not script.is_file():
            return f"技能脚本不存在：{run}"
        completed = subprocess.run(
            [sys.executable, str(script), *run_args.split()],
            cwd=str(path.parent),
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return (completed.stdout or "") + (completed.stderr or "")
    return path.read_text(encoding="utf-8")
