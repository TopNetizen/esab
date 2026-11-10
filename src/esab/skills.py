"""技能清单与核对。

随包技能均为明文，直接扫描包内 data/skills/ 目录。
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from importlib.resources import files


@dataclass(frozen=True)
class SkillRecord:
    path: str
    name: str
    sha256: str
    size: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frontmatter_name(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    block = text[3:end] if end > 0 else ""
    for line in block.splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return ""


def bundled_skills_root() -> Path:
    return Path(str(files("esab").joinpath("data/skills")))


def list_bundled_skills() -> list[SkillRecord]:
    root = bundled_skills_root()
    records = []
    for md in sorted(root.rglob("SKILL.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        records.append(
            SkillRecord(
                path=str(md.relative_to(root)).replace("\\", "/"),
                name=_frontmatter_name(text),
                sha256=sha256_file(md),
                size=md.stat().st_size,
            )
        )
    return records


def verify_bundled() -> dict[str, Any]:
    skills = list_bundled_skills()
    return {
        "skills_root": str(bundled_skills_root()),
        "count": len(skills),
        "skills": [
            {"name": s.name, "path": s.path, "size": s.size, "sha256": s.sha256}
            for s in skills
        ],
    }
