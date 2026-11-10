import json
from pathlib import Path

import esab
from esab.catalog import BUILTIN_SERVERS
from esab.cli import main
from esab.diagnose import read_desktop_marker
from esab.skills import list_bundled_skills, verify_bundled


def test_catalog_has_servers():
    ids = {item["id"] for item in BUILTIN_SERVERS}
    assert {"pkpmmcp", "stsmcp", "jccadmcp", "gbpmcp", "cae-mcp", "plantsmcp", "ssgmcp"} <= ids
    gbp = next(item for item in BUILTIN_SERVERS if item["id"] == "gbpmcp")
    assert gbp["url"] == "http://127.0.0.1:3333/GBPBECA3/galpserver/mcp"


def test_bundled_skills_are_plaintext():
    skills = list_bundled_skills()
    assert len(skills) >= 20
    names = {s.name for s in skills}
    assert "pkpm-link" in names or "PKPM-Link" in names
