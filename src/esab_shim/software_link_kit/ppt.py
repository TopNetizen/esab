"""PPT/PowerPoint/WPS presentation COM bridge."""
from __future__ import annotations

from pathlib import Path
from esab_shim.software_link_kit.office import get_office_app


class PptSession:
    """Lock onto a specific PowerPoint presentation by path."""

    def __init__(self, path: str):
        self.path = str(Path(path).resolve())
        app = get_office_app("PowerPoint")
        if isinstance(app, str):
            raise RuntimeError(app)
        self.app = app
        self.pres = None
        for pres in app.Presentations:
            if pres.FullName.lower() == self.path.lower():
                self.pres = pres
                break
        if self.pres is None:
            self.pres = app.Presentations.Open(self.path, WithWindow=False)

    def finish(self, *, show: bool = True):
        self.pres.Save()
        if not show:
            self.pres.Close()
