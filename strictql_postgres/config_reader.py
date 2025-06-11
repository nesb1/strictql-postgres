import dataclasses
import os
import pathlib
from collections import defaultdict
from pathlib import Path
from typing import Literal

import pydantic
from pydantic import BaseModel, SecretStr
from pydantic_core import ErrorDetails

from strictql_postgres.format_exception import format_exception
from strictql_postgres.queries_to_generate import (
    DataBaseSettings,
    Parameter,
    QueryToGenerate,
    StrictQLQuiriesToGenerate,
)
from strictql_postgres.toml_parser import parse_toml_file


@dataclasses.dataclass()
class StrictqlSettingsLoadError(Exception):
    error: str


class ParsedDatabase(pydantic.BaseModel):  # type: ignore[explicit-any,misc]
    env_name_to_read_connection_url: str


class ParsedStrictqlSettings(BaseModel):  # type: ignore[explicit-any,misc]
    query_files_path: list[str]
    code_generate_dir: str
    databases: dict[str, ParsedDatabase]


class ParsedParameter(BaseModel):  # type: ignore[explicit-any,misc]
    is_optional: bool


class ParsedQueryToGenerate(BaseModel):  # type: ignore[explicit-any,misc]
    query: str
    parameter_names: dict[str, ParsedParameter] = {}
    database: str
    return_type: Literal["list"]
    relative_path: pathlib.Path


class QueryFile(BaseModel):  # type: ignore[explicit-any,misc]
    queries: dict[str, ParsedQueryToGenerate]


@dataclasses.dataclass
class QueryFileContentParserError(Exception):
    error: str


def parse_query_file_content(
    query_file_content: dict[str, object],
) -> dict[str, ParsedQueryToGenerate]:
    try:
        return QueryFile.model_validate(query_file_content).queries
    except pydantic.ValidationError as validation_error:
        error: ErrorDetails
        for error in validation_error.errors():  # type: ignore[misc]
            if error["type"] == "missing":  # type: ignore[misc]
                raise QueryFileContentParserError(
                    error=f"Missing required field: `{'.'.join([str(path_item) for path_item in error['loc']])}`"  # type: ignore[misc]
                )
            raise QueryFileContentParserError(
                error=f"Error when validating section `{'.'.join(str(loc_part) for loc_part in error['loc'])}`, pydantic error: {error['msg']}`"  # type: ignore[misc]
            )

    raise RuntimeError("It should not happen")


def resolve_strictql_settings_from_parsed_settings(
    parsed_settings: ParsedStrictqlSettings,
) -> StrictQLQuiriesToGenerate:
    raise NotImplementedError()


@dataclasses.dataclass
class ExtractStrictqlSettingsError(Exception):
    error: str


class Tool(BaseModel):  # type: ignore[explicit-any,misc]
    strictql_postgres: ParsedStrictqlSettings


class PyprojectToml(BaseModel):  # type: ignore[explicit-any,misc]
    tool: Tool


def extract_strictql_settings_from_parsed_toml_file(
    pyproject_data: dict[str, object],
) -> ParsedStrictqlSettings:
    return PyprojectToml.model_validate(pyproject_data).tool.strictql_postgres
    # except pydantic.ValidationError as e:
    #     for error in e.errors():  # type: ignore[misc]
    #         if error["type"] == "missing":  # type: ignore[misc]
    #             raise ExtractStrictqlSettingsError(
    #                 error=f"Missing `{'.'.join(str(error['loc']))}` section in pyproject.toml"  # type: ignore[misc]
    #             )
    #         if error["loc"] in (("tool",), ("tool", "strictql_postgres")):  # type: ignore[misc]
    #             raise ExtractStrictqlSettingsError(
    #                 error=f"Error when validating section `{'.'.join(str(loc_part) for loc_part in error['loc'])}`, it must be valid toml table`"  # type: ignore[misc]
    #             )
    #
    #         raise ExtractStrictqlSettingsError(
    #             error=f"{error['msg']} for option `{'.'.join(str(loc_part) for loc_part in error['loc'])}` in pyproject.toml"  # type: ignore[misc]
    #         )
    # raise RuntimeError("It should not happen")


@dataclasses.dataclass
class PathValidationError(Exception):
    error: str


def create_path_object_from_str(path_str: str) -> pathlib.Path:
    try:
        return pathlib.Path(path_str)
    except ValueError as error:
        raise PathValidationError(
            error=f"Error when validating path: {format_exception(exception=error)}"
        )


def get_strictql_settings(pyproject_toml_path: Path) -> StrictQLQuiriesToGenerate:
    parsed_toml_file = parse_toml_file(pyproject_toml_path)

    parsed_strictql_settings = extract_strictql_settings_from_parsed_toml_file(
        parsed_toml_file
    )

    code_generation_dir = create_path_object_from_str(
        path_str=parsed_strictql_settings.code_generate_dir
    )

    parsed_query_files: list[dict[str, ParsedQueryToGenerate]] = []
    for query_file_path_str in parsed_strictql_settings.query_files_path:
        query_file_path = pathlib.Path(query_file_path_str)
        parsed_toml_file = parse_toml_file(path=query_file_path)
        parsed_query_files.append(
            parse_query_file_content(query_file_content=parsed_toml_file)
        )

    queries_to_generate: dict[pathlib.Path, dict[str, QueryToGenerate]] = defaultdict(
        dict
    )

    databases = {}
    for database_name, database in parsed_strictql_settings.databases.items():
        databases[database_name] = DataBaseSettings(
            connection_url=SecretStr(
                os.environ[database.env_name_to_read_connection_url]
            )
        )

    for queries_it_query_file in parsed_query_files:
        for query_name, query in queries_it_query_file.items():
            queries_to_generate[code_generation_dir / query.relative_path][
                query_name
            ] = QueryToGenerate(
                query=query.query,
                parameters={
                    parameter_name: Parameter(is_optional=parameter.is_optional)
                    for parameter_name, parameter in query.parameter_names.items()
                },
                database_name=query.database,
                database_connection_url=databases[query.database].connection_url,
                return_type=query.return_type,
            )

    return StrictQLQuiriesToGenerate(
        queries_to_generate=queries_to_generate,
        databases=databases,
        generated_code_path=code_generation_dir,
    )
