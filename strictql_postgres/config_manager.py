import dataclasses
import os
import pathlib
from pathlib import Path
from typing import Literal

import pydantic

from strictql_postgres.format_exception import format_exception
from strictql_postgres.toml_parser import parse_toml_file, TomlParserError
from pydantic import BaseModel, SecretStr, Field, parse_obj_as, TypeAdapter


class ParsedDatabase(pydantic.BaseModel):
    env_name_to_read_connection_url: str


class ParsedStrictqlSettings(BaseModel):  # type: ignore[explicit-any,misc]
    query_files_path: list[str]
    code_generate_dir: str
    databases: dict[str, ParsedDatabase]


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


class ParsedParameter(BaseModel):
    is_optional: bool


class ParsedQueryToGenerate(BaseModel):
    query: str
    parameter_names: dict[str, ParsedParameter]
    database: str
    return_type: Literal["list"]
    function_name: str


class QueryFile(BaseModel):
    queries: dict[str, ParsedQueryToGenerate]


@dataclasses.dataclass
class QueryFileContentParserError(Exception):
    error: str


def parse_query_file_content(
    query_file_content: dict[str, object],
) -> dict[str, ParsedQueryToGenerate]:
    try:
        return QueryFile.model_validate(query_file_content).queries
    except pydantic.ValidationError as error:
        for error in error.errors():
            if error["type"] == "missing":
                raise QueryFileContentParserError(
                    error=f"Missing required field: `{'.'.join([
                    str(path_item)
                    for path_item in error["loc"]
                ])}`"
                )
            raise QueryFileContentParserError(
                error=f'Error when validating section `{".".join(str(loc_part) for loc_part in error["loc"])}`, pydantic error: {error["msg"]}`'
            )

    raise RuntimeError("It should not happen")


def resolve_strictql_settings_from_parsed_settings(
    parsed_settings: ParsedStrictqlSettings,
) -> StrictqlSettings:
    raise NotImplementedError()


@dataclasses.dataclass
class ExtractStrictqlSettingsError(Exception):
    error: str


class Tool(BaseModel):
    strictql_postgres: ParsedStrictqlSettings


class PyprojectToml(BaseModel):
    tool: Tool


def extract_strictql_settings_from_parsed_toml_file(
    pyproject_data: dict[str, object],
) -> ParsedStrictqlSettings:

    try:
        return PyprojectToml.model_validate(pyproject_data).tool.strictql_postgres
    except pydantic.ValidationError as e:

        for error in e.errors():
            if error["type"] == "missing":
                raise ExtractStrictqlSettingsError(
                    error=f"Missing `{".".join(error['loc'])}` section in pyproject.toml"
                )
            if error["loc"] in (("tool",), ("tool", "strictql_postgres")):
                raise ExtractStrictqlSettingsError(
                    error=f'Error when validating section `{".".join(str(loc_part) for loc_part in error["loc"])}`, it must be valid toml table`'
                )

            raise ExtractStrictqlSettingsError(
                error=f"{error['msg']} for option `{".".join(str(loc_part) for loc_part in error['loc'])}` in pyproject.toml"
            )
    raise RuntimeError("It should not happen")


@dataclasses.dataclass
class PathValidationError(Exception):
    error: str


def create_path_object_from_str(path_str: str) -> pathlib.Path:

    try:
        return pathlib.Path(path_str)
    except ValueError as error:
        raise PathValidationError(
            error=f"Error when validating path: {format_exception(
            exception=error,
        )}"
        )


def resolve_strictql_settings(
        code_generation_directory: pathlib.Path,
        parsed_query_files: list[]
)


def parse_strictql_settings(pyproject_toml_path: Path | None) -> StrictqlSettings:
    if pyproject_toml_path is None:
        pyproject_toml_path = pathlib.Path(os.getcwd()) / "pyproject.toml"

    parsed_toml_file = parse_toml_file(pyproject_toml_path)

    parsed_strictql_settings = extract_strictql_settings_from_parsed_toml_file(
        parsed_toml_file
    )

    code_generation_dir = create_path_object_from_str(
        path_str=parsed_strictql_settings.code_generate_dir
    )

    query_files_path = []

    for query_file_path in parsed_strictql_settings.query_files_path:
        query_files_path.append(create_path_object_from_str(path_str=query_file_path))

    parsed_query_files = []
    for query_file_path in query_files_path:
        parsed_toml_file = parse_toml_file(path=query_file_path)
        parsed_query_files.append(
            parse_query_file_content(query_file_content=parsed_toml_file)
        )

    # validate paths
    # parse query files
    pass
