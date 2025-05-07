import dataclasses
from typing import Mapping

from strictql_postgres.python_types import ALL_TYPES


@dataclasses.dataclass(frozen=True)
class ColumnType:
    type_: type[object]
    is_optional: bool


ColumnName = str


@dataclasses.dataclass
class BindParam:
    name_in_function: str
    type_: ALL_TYPES


BindParams = list[BindParam]


@dataclasses.dataclass(frozen=True)
class NotEmptyRowSchema:
    schema: Mapping[ColumnName, ALL_TYPES]

    def __post_init__(self) -> None:
        if len(self.schema) == 0:
            raise ValueError("Empty schema")
