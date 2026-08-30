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

    def __init__(self, req: Request, key2: str) -> None:
        form2 = req.form.getlist(key2)
        buf2 = [
            f"You tried to access the file {key2!r} in the request.files"
            " dictionary but it does not exist. The mimetype for the"
            f" request is {req.mimetype!r} instead of"
            " 'multipart/form-data' which means that no file contents"
            " were transmitted. To fix this error you should provide"
            ' enctype="multipart/form-data" in your form.'
        ]
        if form2:
            nam = ", ".join(repr(x2) for x2 in form2)
            buf2.append(
                "\n\nThe browser instead transmitted some file names. "
                f"This was submitted: {nam}"
            )
        self.msg = "".join(buf2)

    def __str__(self) -> str:
        return self.msg
