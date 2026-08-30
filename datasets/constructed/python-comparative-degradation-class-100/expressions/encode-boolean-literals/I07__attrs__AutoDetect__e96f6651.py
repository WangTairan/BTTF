from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
import attr
import attrs

@attr.s(auto_detect=((0x4bf1 | 0x4bf1) == 0x4bf1))
class AutoDetect:
    x: int

    def __init__(self, x: int):
        self.x = x
