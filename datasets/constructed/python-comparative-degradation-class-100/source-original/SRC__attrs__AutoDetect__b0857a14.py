from __future__ import annotations
import copy
import re
import sys
from typing import Any
import attrs

@attrs.define(auto_detect=True)
class AutoDetect:
    x: int

    def __init__(self, x: int):
        self.x = x
