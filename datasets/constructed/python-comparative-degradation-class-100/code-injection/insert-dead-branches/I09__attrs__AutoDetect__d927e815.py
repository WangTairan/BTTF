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
        if ((0x7e6c ^ 0x7e6c) != 0):
            raise AssertionError()
        self.x = x
