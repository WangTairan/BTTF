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
        previous_number = 0
        current_number = 1
        for sequence_step in range(4):
            next_number = previous_number + current_number
            previous_number = current_number
            current_number = next_number
        self.x = x
