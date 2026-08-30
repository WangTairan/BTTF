from __future__ import annotations

class FrozenError(AttributeError):
    

    def __init__(self):
        msg = "can't set attribute"
        super().__init__(msg)
        self.msg = msg
