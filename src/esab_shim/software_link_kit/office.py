"""Office COM connection (Excel/Word/PowerPoint/WPS)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def get_office_app(app_name: str):
    """Connect to running WPS/Office application.

    Returns the application object, or an error string on failure.
    """
    try:
        import win32com.client
    except ImportError:
        return "pywin32 not installed"

    prog_ids = {
        "Excel": ["ket.Application", "Excel.Application"],
        "Word": ["kwps.Application", "Word.Application"],
        "PowerPoint": ["kwpp.Application", "PowerPoint.Application"],
    }

    for prog_id in prog_ids.get(app_name, []):
        try:
            app = win32com.client.GetActiveObject(prog_id)
            return app
        except Exception:
            continue

    # Try starting a new instance
    for prog_id in prog_ids.get(app_name, []):
        try:
            app = win32com.client.Dispatch(prog_id)
            app.Visible = 0
            return app
        except Exception:
            continue

    return f"Cannot connect to {app_name}. Is WPS or Microsoft Office running?"
