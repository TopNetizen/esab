"""User skill directory paths."""
from pathlib import Path

USER_SKILLS_DIR = Path.home() / ".esab" / "skills"
PLUGINS_DIR = Path.home() / ".esab" / "plugins"


def read_skill_frontmatter(skill_md: str) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    import re
    text = Path(skill_md).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    result = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip()
    return result


def skills_roots() -> list[Path]:
    """Return all skill root directories."""
    roots = [USER_SKILLS_DIR]
    return roots
