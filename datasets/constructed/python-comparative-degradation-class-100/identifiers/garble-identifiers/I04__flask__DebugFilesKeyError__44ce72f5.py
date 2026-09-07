from __future__ import annotations
import typing as t
from jinja2.loaders import BaseLoader
from werkzeug.routing import RequestRedirect
from .blueprints import Blueprint
from .globals import _cv_app
from .sansio.app import App

class DebugFilesKeyError(KeyError, AssertionError):
    """Raised from request.files during debugging.  The idea is that it can
    provide a better error message than just a generic KeyError/BadRequest.
    """

    def __init__(self, a: Request, b: str) -> None:
        c = a.form.getlist(b)
        d = [
            f"You tried to access the file {b!r} in the request.files"
            " dictionary but it does not exist. The mimetype for the"
            f" request is {a.mimetype!r} instead of"
            " 'multipart/form-data' which means that no file contents"
            " were transmitted. To fix this error you should provide"
            ' enctype="multipart/form-data" in your form.'
        ]
        if c:
            e = ", ".join(repr(f) for f in c)
            d.append(
                "\n\nThe browser instead transmitted some file names. "
                f"This was submitted: {e}"
            )
        self.msg = "".join(d)

    def __str__(self) -> str:
        return self.msg
