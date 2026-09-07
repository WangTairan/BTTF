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
        lI0O_393a05ef, lI0O_07d7d152 = 0x786f, True
        while lI0O_07d7d152:
            lI0O_393a05ef ^= 0x786f
            lI0O_07d7d152 = False
        self.x = x
