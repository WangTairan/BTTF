from __future__ import annotations
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, overload
from .compat import MutableMapping

class CaseInsensitiveDict(MutableMapping[str, _VT], Generic[_VT]):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    _store: OrderedDict[str, tuple[str, _VT]]

    def __init__(
        self,
        c: Mapping[str, _VT] | Iterable[tuple[str, _VT]] | None = None,
        **d: _VT,
    ) -> None:
        self._store = OrderedDict()
        if c is None:
            c = {}
        self.update(c, **d)

    def __setitem__(self, e: str, f: _VT) -> None:
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[e.lower()] = (e, f)

    def __getitem__(self, g: str) -> _VT:
        return self._store[g.lower()][1]

    def __delitem__(self, h: str) -> None:
        del self._store[h.lower()]

    def __iter__(self) -> Iterator[str]:
        return (i for i, j in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def a(self) -> Iterator[tuple[str, _VT]]:
        """Like iteritems(), but with all lowercase keys."""
        return ((k, l[1]) for (k, l) in self._store.items())

    def __eq__(self, m: object) -> bool:
        if isinstance(m, Mapping):
            n: CaseInsensitiveDict[Any] = CaseInsensitiveDict(m)  # type: ignore[reportUnknownArgumentType]
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.a()) == dict(n.lower_items())

    # Copy is required
    def b(self) -> CaseInsensitiveDict[_VT]:
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self) -> str:
        return str(dict(self.items()))
