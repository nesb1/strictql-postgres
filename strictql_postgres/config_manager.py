import pathlib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, SecretStr


def find_pyproject_toml_file(current_working_dir: Path) -> Path:
    raise NotImplementedError()


class ParsedStrictqlSettings(BaseModel):  # type: ignore[explicit-any,misc]
    query_files: list[str]
    code_generate_dir: str


def parse_pyproject_toml_strictql_tool(path: Path) -> ParsedStrictqlSettings:
    raise NotImplementedError()


class DataBaseSettings(BaseModel):  # type: ignore[explicit-any,misc]
    name: str
    connection_url: SecretStr


class Parameter(BaseModel):  # type: ignore[explicit-any,misc]
    name: str
    is_optional: bool


class QueryToGenerate(BaseModel):  # type: ignore[explicit-any,misc]
    query: str
    name: str
    parameter_names: list[Parameter]
    database: DataBaseSettings
    return_type: Literal["list"]
    function_name: str


class StrictqlSettings(BaseModel):  # type: ignore[explicit-any,misc]
    queries_to_generate: dict[pathlib.Path, QueryToGenerate]
    databases: dict[str, DataBaseSettings]
    generated_code_path: pathlib.Path


def resolve_strictql_settings_from_parsed_settings(
    parsed_settings: ParsedStrictqlSettings,
) -> StrictqlSettings:
    raise NotImplementedError()
