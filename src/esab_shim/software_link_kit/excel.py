"""Excel/WPS spreadsheet COM bridge."""
from __future__ import annotations

import os
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from esab_shim.software_link_kit.office import get_office_app


class ExcelSession:
    """Lock onto a specific Excel workbook by path."""

    def __init__(self, path: str, *, save_as: str | None = None):
        self.path = str(Path(path).resolve())
        self.save_as = save_as
        self.app = None
        self.wb = None
        self.backup = None
        self._original_screen_updating = None
        self._original_display_alerts = None
        self._connect()

    def _connect(self):
        app = get_office_app("Excel")
        if isinstance(app, str):
            raise RuntimeError(app)
        self.app = app
        self._original_screen_updating = app.ScreenUpdating
        self._original_display_alerts = app.DisplayAlerts
        app.ScreenUpdating = False

        target_name = Path(self.path).name
        for wb in app.Workbooks:
            if wb.FullName.lower() == self.path.lower():
                self.wb = wb
                break
        if self.wb is None:
            self.wb = app.Workbooks.Open(self.path)

        # Backup
        self.backup = self.path + ".bak"
        try:
            shutil.copy2(self.path, self.backup)
        except OSError:
            self.backup = None

    @classmethod
    def new(cls, path: str, *, template: str | None = None, overwrite: bool = False):
        p = Path(path)
        if p.exists() and not overwrite:
            raise FileExistsError(f"File exists: {path}")
        if p.exists() and overwrite:
            try:
                p.unlink()
            except OSError:
                pass
        app = get_office_app("Excel")
        if isinstance(app, str):
            raise RuntimeError(app)
        wb = app.Workbooks.Add()
        if template:
            wb = app.Workbooks.Add(template)
        wb.SaveAs(str(p.resolve()))
        return cls(str(p.resolve()))

    @classmethod
    def bind(cls, wb, *, save_as: str | None = None):
        obj = cls.__new__(cls)
        obj.app = wb.Application
        obj.wb = wb
        obj.path = wb.FullName
        obj.save_as = save_as
        obj.backup = None
        return obj

    @contextmanager
    def quiet(self):
        self.app.DisplayAlerts = False
        try:
            yield
        finally:
            self.app.DisplayAlerts = self._original_display_alerts

    def finish(self, *, show: bool = True):
        if self.save_as:
            self.wb.SaveAs(self.save_as)
        else:
            self.wb.Save()
        self.app.ScreenUpdating = self._original_screen_updating
        self.app.DisplayAlerts = self._original_display_alerts
        if show:
            self.wb.Activate()
        else:
            self.wb.Close(SaveChanges=0)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.finish(show=True)


def get_used_range(sheet) -> Any:
    return sheet.UsedRange
