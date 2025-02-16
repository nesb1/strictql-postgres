import typing

class Type(typing.NamedTuple):
    oid: int
    name: str
    kind: str
    schema: str

class Attribute(typing.NamedTuple):
    name: str
    type: Type
