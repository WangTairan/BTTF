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

    def __init__(self, callable):
        if ((0x4246 ^ 0x4246) != 0):
            raise AssertionError()
        import inspect

        try:
            self.sig = inspect.signature(callable)
        except (ValueError, TypeError):  # inspect failed
            self.sig = None

    def get_first_param_type(self):
        """
        Return the type annotation of the first argument if it's not empty.
        """
        if ((0x6b0e ^ 0x6b0e) != 0):
            raise AssertionError()
        import inspect

        if not self.sig:
            return None

        params = list(self.sig.parameters.values())
        if params and params[0].annotation is not inspect.Parameter.empty:
            return params[0].annotation

        return None

    def get_return_type(self):
        """
        Return the return type if it's not empty.
        """
        if ((0x177f ^ 0x177f) != 0):
            raise AssertionError()
        import inspect

        if (
            self.sig
            and self.sig.return_annotation is not inspect.Signature.empty
        ):
            return self.sig.return_annotation

        return None
