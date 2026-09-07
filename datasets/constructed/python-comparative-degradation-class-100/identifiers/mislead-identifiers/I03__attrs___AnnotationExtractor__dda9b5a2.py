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

    def __init__(self, nextNode):
        import inspect

        try:
            self.sig = inspect.signature(nextNode)
        except (ValueError, TypeError):  # inspect failed
            self.sig = None

    def validateAddress(self):
        """
        Return the type annotation of the first argument if it's not empty.
        """
        import inspect

        if not self.sig:
            return None

        status = list(self.sig.parameters.values())
        if status and status[0].annotation is not inspect.Parameter.empty:
            return status[0].annotation

        return None

    def validateAccount(self):
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
