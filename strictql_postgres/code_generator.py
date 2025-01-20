import dataclasses
from typing import Literal

ColumnName = str
ColumnType = type[object]

DataBaseRowModel = dict[ColumnName, ColumnType]


@dataclasses.dataclass
class QueryWithDBInfo:
    query: str
    query_result_row_model: DataBaseRowModel


@dataclasses.dataclass
class StrictQLGeneratedCode:
    imports: str
    model_definition: str
    function_definition: str


def generate_code_for_query(
    query_with_db_info: QueryWithDBInfo,
    execution_variant: Literal["fetch_all"],
    function_name: str,
) -> str:
    imports = """from pydantic import BaseModel
from asyncpg import Connection
from collections.abc import Sequence

from strictql_postgres.asyncpg_result_converter import (
    convert_records_to_pydantic_models,
)
"""
    model_name = "Model"
    fields_definitions = []
    for column_name, column_type in query_with_db_info.query_result_row_model.items():
        type_name: object = getattr(column_type, "__name__", None)
        if type_name is None or not isinstance(type_name, str):
            raise NotImplementedError()
        fields_definitions.append(f"    {column_name}: {type_name}")
    field_definitions_as_str = "\n".join(fields_definitions)
    model_definition = f"""class {model_name}(BaseModel):
{field_definitions_as_str}
"""
    function_definition = f"""async def {function_name}(connection: Connection) -> Sequence[{model_name}]:
    records = await connection.fetch("{query_with_db_info.query}")
    return convert_records_to_pydantic_models(records=records, pydantic_type={model_name})"""
    return f"{imports}\n\n{model_definition}\n\n{function_definition}\n"
