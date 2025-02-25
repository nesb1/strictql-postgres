import dataclasses
from typing import Mapping


@dataclasses.dataclass(frozen=True)
class ColumnType:
    type_: type[object]
    is_optional: bool


ColumnName = str
DataBaseRowModel = dict[ColumnName, ColumnType]


@dataclasses.dataclass
class BindParam:
    name_in_function: str
    type_: type[object]


BindParams = list[BindParam]


@dataclasses.dataclass()
class SupportedQuery:
    query: str

    def __post_init__(self) -> None:
        if not self.query.lower().strip().startswith(("select", "delete")):
            raise ValueError(f"Query: {self.query} not supported")


@dataclasses.dataclass(frozen=True)
class NotEmptyRowSchema:
    schema: Mapping[ColumnName, ColumnType]

    def __post_init__(self) -> None:
        if len(self.schema) == 0:
            raise ValueError("Empty schema")


@dataclasses.dataclass
class QueryWithDBInfo:
    query: SupportedQuery
    result_row_model: DataBaseRowModel
    params: BindParams
