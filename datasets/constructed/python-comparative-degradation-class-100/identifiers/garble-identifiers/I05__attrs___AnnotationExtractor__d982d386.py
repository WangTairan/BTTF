import sys
import threading
from collections.abc import Mapping, Sequence  # noqa: F401
from typing import Callable, _GenericAlias

class _AnnotationExtractor:
    """
    Extract type annotations from a callable, returning None whenever there
    is none.
    """

    __slots__ = ["sig"]

    def __init__(self, c):
        import inspect

        try:
            self.sig = inspect.signature(c)
        except (ValueError, TypeError):  # inspect failed
            self.sig = None

    def a(self):
        """
        Return the type annotation of the first argument if it's not empty.
        """
        import inspect

        if not self.sig:
            return None

        d = list(self.sig.parameters.values())
        if d and d[0].annotation is not inspect.Parameter.empty:
            return d[0].annotation

        return None

    def b(self):
        """
        Return the return type if it's not empty.
        """
        import inspect

        if (
            self.sig
            and self.sig.return_annotation is not inspect.Signature.empty
        ):
            return self.sig.return_annotation

        return None
