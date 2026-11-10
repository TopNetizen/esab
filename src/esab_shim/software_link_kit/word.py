"""Word/WPS document COM bridge."""
from __future__ import annotations

import shutil
from contextlib import contextmanager
from pathlib import Path
from esab_shim.software_link_kit.office import get_office_app


class WordSession:
    """Lock onto a specific Word document by path."""

    def __init__(self, path: str, *, save_as: str | None = None):
        self.path = str(Path(path).resolve())
        self.save_as = save_as
        app = get_office_app("Word")
        if isinstance(app, str):
            raise RuntimeError(app)
        self.app = app
        self.doc = None
        for doc in app.Documents:
            if doc.FullName.lower() == self.path.lower():
                self.doc = doc
                break
        if self.doc is None:
            self.doc = app.Documents.Open(self.path, Visible=False)

    @contextmanager
    def open(self):
        try:
            yield self.doc
        finally:
            self.doc.Save()

    def finish(self, *, show: bool = True):
        self.doc.Save()
        if self.save_as:
            self.doc.SaveAs(self.save_as)
        if not show:
            self.doc.Close(SaveChanges=0)


class DocxFile:
    """Direct python-docx wrapper for file editing."""

    def __init__(self, path: str):
        from docx import Document
        self.path = path
        self.doc = Document(path)

    @classmethod
    def new(cls, path: str, *, template: str | None = None, overwrite: bool = False):
        from docx import Document
        p = Path(path)
        if p.exists() and not overwrite:
            raise FileExistsError(f"File exists: {path}")
        if template:
            doc = Document(template)
        else:
            doc = Document()
        obj = cls.__new__(cls)
        obj.path = path
        obj.doc = doc
        return obj

    def save(self):
        self.doc.save(self.path)
