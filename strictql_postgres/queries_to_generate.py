import pathlib
from typing import Literal

from pydantic import BaseModel, SecretStr


class DataBaseSettings(BaseModel):  # type: ignore[explicit-any,misc]
    connection_url: SecretStr


class Parameter(BaseModel):  # type: ignore[explicit-any,misc]
    is_optional: bool


class QueryToGenerate(BaseModel):  # type: ignore[explicit-any,misc]
    query: str
    parameters: dict[str, Parameter]
    database_name: str
    database_connection_url: SecretStr
    return_type: Literal["list"]
    function_name: str


class QueryToGenerateWithSourceInfo(BaseModel):  # type: ignore[explicit-any,misc]
    query_to_generate: QueryToGenerate
    query_file_path: pathlib.Path
    query_name: str


class StrictQLQueriesToGenerate(BaseModel):  # type: ignore[explicit-any,misc]
    queries_to_generate: dict[pathlib.Path, QueryToGenerate]
    databases: dict[str, DataBaseSettings]
    generated_code_path: pathlib.Path
