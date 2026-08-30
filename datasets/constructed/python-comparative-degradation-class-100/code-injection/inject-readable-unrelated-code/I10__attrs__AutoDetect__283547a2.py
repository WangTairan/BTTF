from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
import attr
import attrs

@attr.s(auto_detect=True)
class AutoDetect:
    x: int

    def __init__(self, x: int):
        morning_temperature = 18
        evening_temperature = 14
        lower_temperature = morning_temperature
        if evening_temperature < lower_temperature:
            lower_temperature = evening_temperature
        self.x = x
