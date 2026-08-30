from __future__ import annotations

class FrozenError(AttributeError):
    """
    Copy *self* and apply *changes*. This
    works similarly to `attrs.evolve` but that

    function does not work with :class:`attrs.Attribute`.
    It is mainly meant to be used for

    `transform-fields`. .. versionadded:: 20.3.0
    """

    def __init__(self):
        msg = "can't set attribute"
        super().__init__(msg)
        self.msg = msg
