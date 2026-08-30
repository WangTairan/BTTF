from __future__ import annotations
from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Generic, TypeVar, overload
from .compat import MutableMapping

class CaseInsensitiveDict(MutableMapping[str, _VT], Generic[_VT]):
    

    _store: OrderedDict[str, tuple[str, _VT]]

    def __init__(
        self,
        data: Mapping[str, _VT] | Iterable[tuple[str, _VT]] | None = None,
        **kwargs: _VT,
    ) -> None:
        self._store = OrderedDict()
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key: str, value: _VT) -> None:
         
         
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key: str) -> _VT:
        return self._store[key.lower()][1]

    def __delitem__(self, key: str) -> None:
        del self._store[key.lower()]

    def __iter__(self) -> Iterator[str]:
        return (casedkey for casedkey, _ in self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def lower_items(self) -> Iterator[tuple[str, _VT]]:
        
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Mapping):
            other_dict: CaseInsensitiveDict[Any] = CaseInsensitiveDict(other)   
        else:
            return NotImplemented
         
        return dict(self.lower_items()) == dict(other_dict.lower_items())

     
    def copy(self) -> CaseInsensitiveDict[_VT]:
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self) -> str:
        return str(dict(self.items()))
