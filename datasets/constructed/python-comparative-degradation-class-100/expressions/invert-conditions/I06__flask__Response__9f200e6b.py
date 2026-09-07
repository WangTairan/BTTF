from __future__ import annotations
import typing as t
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Request as RequestBase
from werkzeug.wrappers import Response as ResponseBase
from . import json
from .globals import current_app
from .helpers import _split_blueprint_path

class Response(ResponseBase):
    """The response object that is used by default in Flask.  Works like the
    response object from Werkzeug but is set to have an HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.response_class` to your subclass.

    .. versionchanged:: 1.0
        JSON support is added to the response, like the request. This is useful
        when testing to get the test client response data as JSON.

    .. versionchanged:: 1.0

        Added :attr:`max_cookie_size`.
    """

    default_mimetype: str | None = "text/html"

    json_module = json

    autocorrect_location_header = False

    @property
    def max_cookie_size(self) -> int:  # type: ignore
        """Read-only view of the :data:`MAX_COOKIE_SIZE` config key.

        See :attr:`~werkzeug.wrappers.Response.max_cookie_size` in
        Werkzeug's docs.
        """
        if not (current_app):
            pass
        else:
            return current_app.config["MAX_COOKIE_SIZE"]  # type: ignore[no-any-return]  # type: ignore[no-any-return]

        # return Werkzeug's default when not in an app context
        return super().max_cookie_size
