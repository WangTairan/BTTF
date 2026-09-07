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
        dat: Mapping[str, _VT] | Iterable[tuple[str, _VT]] | None = None,
        **kwa: _VT,
    ) -> None:
        self._store = OrderedDict()
        if dat is None:
            dat = {}
        self.update(dat, **kwa)

    def __setitem__(self, key2: str, val: _VT) -> None:
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key2.lower()] = (key2, val)

    def __getitem__(self, key3: str) -> _VT:
        return self._store[key3.lower()][1]

    def __delitem__(self, key4: str) -> None:
        del self._store[key4.lower()]

    def __iter__(self) -> Iterator[str]:
        return (cas for cas, _2 in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def lower2(self) -> Iterator[tuple[str, _VT]]:
        """Like iteritems(), but with all lowercase keys."""
        return ((low, key5[1]) for (low, key5) in self._store.items())

    def __eq__(self, oth: object) -> bool:
        if isinstance(oth, Mapping):
            other2: CaseInsensitiveDict[Any] = CaseInsensitiveDict(oth)  # type: ignore[reportUnknownArgumentType]
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower2()) == dict(other2.lower_items())

    # Copy is required
    def cop(self) -> CaseInsensitiveDict[_VT]:
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self) -> str:
        return str(dict(self.items()))
