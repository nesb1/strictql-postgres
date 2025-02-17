import dataclasses


@dataclasses.dataclass(frozen=True)
class ColumnType:
    type_: type[object]
    is_optional: bool


ColumnName = str
DataBaseRowModel = dict[ColumnName, ColumnType]


@dataclasses.dataclass
class QueryParam:
    name_in_function: str
    type_: type[object]


QueryParams = list[QueryParam]


@dataclasses.dataclass()
class SelectQuery:
    query: str

    def __post_init__(self) -> None:
        if not self.query.lower().strip().startswith("select"):
            raise ValueError()


@dataclasses.dataclass
class QueryWithDBInfo:
    query: SelectQuery
    result_row_model: DataBaseRowModel
    params: QueryParams
