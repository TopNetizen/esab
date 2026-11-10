"""测试技能扫描与明文索引。"""

from pathlib import Path

from esab.skill_vault import read_skill_tree


def test_read_skill_tree_finds_skills(tmp_path: Path):
    (tmp_path / "demo").mkdir()
    (tmp_path / "demo" / "SKILL.md").write_text(
        "---\nname: demo-link\n---\n# Demo\n", encoding="utf-8"
    )
    skills = read_skill_tree(tmp_path)
    assert len(skills) == 1
    assert skills[0].name == "demo-link"
    assert "demo/SKILL.md" in skills[0].relative_path
