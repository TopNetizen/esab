"""技能目录扫描与明文输出。

随包分发的技能文件均为明文。
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path


def connect_db(db_path: Path) -> sqlite3.Connection:
    """以只读模式打开 SQLite 数据库。"""
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


@dataclass
class BundledSkill:
    relative_path: str
    name: str
    content_hash: str
    body_bytes: int
    loaded: str


def _frontmatter_name(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        block = text[3:end] if end > 0 else ""
        for line in block.splitlines():
            if line.startswith("name:"):
                return line.split(":", 1)[1].strip().strip("\"'")
    return ""


def read_skill_tree(skills_root: Path) -> list[BundledSkill]:
    """扫描技能目录下全部 .md 文件。"""
    loaded: list[BundledSkill] = []
    for path in sorted(skills_root.rglob("*.md")):
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        body = text
        relative = path.relative_to(skills_root).as_posix()
        loaded.append(
            BundledSkill(
                relative_path=relative,
                name=_frontmatter_name(text),
                content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                body_bytes=len(body),
                loaded=body,
            )
        )
    return loaded


def write_skill(skills: list[BundledSkill], out_dir: Path) -> None:
    for skill in skills:
        target = out_dir / skill.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(skill.loaded, encoding="utf-8")


def dump_public_json(skills: list[BundledSkill]) -> str:
    import json

    rows = [
        {
            "path": s.relative_path,
            "name": s.name,
            "bytes": s.body_bytes,
            "sha256": s.content_hash,
        }
        for s in skills
    ]
    return json.dumps({"count": len(skills), "skills": rows}, ensure_ascii=False, indent=2)
