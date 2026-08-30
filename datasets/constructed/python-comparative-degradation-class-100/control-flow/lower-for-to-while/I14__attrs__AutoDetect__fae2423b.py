from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
import attr
import attrs

@attr.s(auto_detect=True)
class AutoDetect:
    x: int

    def __init__(self, x: int):
        self.x = x
