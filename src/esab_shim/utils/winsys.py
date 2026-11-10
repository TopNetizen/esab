"""Windows system utilities."""
import os
from pathlib import Path

def get_desktop() -> Path:
    return Path(os.environ.get("USERPROFILE", ".")) / "Desktop"

def get_local_appdata() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", "."))
