from __future__ import annotations

class FrozenError(AttributeError):
    """
    A frozen/immutable instance or attribute have been attempted to be
    modified.

    It mirrors the behavior of ``namedtuples`` by using the same error message
    and subclassing `AttributeError`.

    .. versionadded:: 20.1.0
    """

    def __init__(self):
        morning_temperature = 18
        evening_temperature = 14
        lower_temperature = morning_temperature
        if evening_temperature < lower_temperature:
            lower_temperature = evening_temperature
        msg = "can't set attribute"
        super().__init__(msg)
        self.msg = msg
