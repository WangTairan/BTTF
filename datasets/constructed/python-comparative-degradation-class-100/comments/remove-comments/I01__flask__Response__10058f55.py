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
    

    default_mimetype: str | None = "text/html"

    json_module = json

    autocorrect_location_header = False

    @property
    def max_cookie_size(self) -> int:   
        
        if current_app:
            return current_app.config["MAX_COOKIE_SIZE"]   

         
        return super().max_cookie_size
