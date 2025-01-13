import typing

class Type(typing.NamedTuple):
    oid: int
    name: str
    kind: str
    schema: str

class Attribute(typing.NamedTuple):
    name: str
    type: Type

class _RangeValue(typing.Protocol):
    def __eq__(self, __value: object) -> bool: ...
    def __lt__(self, __other: "_RangeValue") -> bool: ...
    def __gt__(self, __other: "_RangeValue") -> bool: ...

_RV = typing.TypeVar("_RV", bound=_RangeValue)

class Range(typing.Generic[_RV]):
    @property
    def upper(self) -> _RV | None: ...
    @property
    def lower(self) -> _RV | None: ...
