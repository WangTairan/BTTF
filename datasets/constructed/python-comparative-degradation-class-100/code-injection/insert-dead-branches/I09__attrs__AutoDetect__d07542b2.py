from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
import attr
import attrs

@attr.s(auto_detect=True)
class AutoDetect:
    x: int

    def __init__(self, x: int):
        if ((0x928e ^ 0x928e) != 0):
            raise AssertionError()
        self.x = x
