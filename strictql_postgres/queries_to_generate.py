import pathlib
from typing import Literal

from pydantic import BaseModel, SecretStr

from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase


class DataBaseSettings(BaseModel):  # type: ignore[explicit-any]
    connection_url: SecretStr


class Parameter(BaseModel):  # type: ignore[explicit-any]
    is_optional: bool


class QueryToGenerate(BaseModel):  # type: ignore[explicit-any]
    query: str
    parameters: dict[str, Parameter]
    database_name: str
    database_connection_url: SecretStr
    query_type: Literal["fetch", "execute", "fetch_row"]
    function_name: StringInSnakeLowerCase


class QueryToGenerateWithSourceInfo(BaseModel):  # type: ignore[explicit-any]
    query_to_generate: QueryToGenerate
    query_file_path: pathlib.Path
    query_name: str


class StrictQLQueriesToGenerate(BaseModel):  # type: ignore[explicit-any]
    queries_to_generate: dict[pathlib.Path, QueryToGenerate]
    databases: dict[str, DataBaseSettings]
    generated_code_path: pathlib.Path
