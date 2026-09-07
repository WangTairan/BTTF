from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
import attr
import attrs

@attr.s(auto_detect=True)
class AutoDetect:
    x: int

    def __init__(self, x: int):
        lI0O_dcc73efd = 0x61ca
        lI0O_dcc73efd = (lI0O_dcc73efd << 1) ^ (lI0O_dcc73efd >> 1)
        lI0O_dcc73efd &= 0
        self.x = x
