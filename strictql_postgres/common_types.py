import dataclasses
from typing import Mapping


@dataclasses.dataclass(frozen=True)
class ColumnType:
    type_: type[object]
    is_optional: bool


ColumnName = str


@dataclasses.dataclass
class BindParam:
    name_in_function: str
    type_: type[object]
    is_optional: bool


BindParams = list[BindParam]


@dataclasses.dataclass(frozen=True)
class NotEmptyRowSchema:
    schema: Mapping[ColumnName, ColumnType]

    def __post_init__(self) -> None:
        if len(self.schema) == 0:
            raise ValueError("Empty schema")
