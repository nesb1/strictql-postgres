import dataclasses
import pathlib
import tomllib
from collections import defaultdict
from typing import Literal, Mapping, TypeVar

import pydantic
from pydantic import BaseModel, SecretStr

from strictql_postgres.dataclass_error import Error
from strictql_postgres.queries_to_generate import (
    DataBaseSettings,
    Parameter,
    QueryToGenerate,
    QueryToGenerateWithSourceInfo,
    StrictQLQueriesToGenerate,
)
from strictql_postgres.string_in_snake_case import (
    StringInSnakeLowerCase,
    StringNotInLowerSnakeCase,
)


class ParsedDatabase(pydantic.BaseModel):  # type: ignore[explicit-any]
    env_name_to_read_connection_url: str


class ParsedStrictqlSettings(pydantic.BaseModel):  # type: ignore[explicit-any]
    query_files_path: list[str]
    code_generate_dir: str
    databases: dict[str, ParsedDatabase]


class ParsedParameter(pydantic.BaseModel):  # type: ignore[explicit-any]
    is_optional: bool


class ParsedQueryToGenerate(pydantic.BaseModel):  # type: ignore[explicit-any]
    query: str
    parameter_names: dict[str, ParsedParameter] = {}
    database: str
    query_type: Literal["fetch", "execute", "fetch_row"]
    relative_path: str


class QueryFileContentModel(pydantic.BaseModel):  # type: ignore[explicit-any]
    queries: dict[str, ParsedQueryToGenerate]


class PyprojectTomlWithStrictQLToolSettings(pydantic.BaseModel):  # type: ignore[explicit-any]
    strictql_postgres: ParsedStrictqlSettings


class ParsedPyprojectTomlWithStrictQLSection(pydantic.BaseModel):  # type: ignore[explicit-any]
    tool: PyprojectTomlWithStrictQLToolSettings


@dataclasses.dataclass(frozen=True)
class DataClassError(Exception):
    error: str

    def __str__(self) -> str:
        return self.error


class GetStrictQLQueriesToGenerateError(DataClassError):
    pass


T = TypeVar("T", bound=BaseModel)


class ParseTomlFileAsModelError(Error):
    pass


def parse_toml_file_as_model(path: pathlib.Path, model_type: type[T]) -> T:
    if not path.exists():
        raise ParseTomlFileAsModelError(error=f"File `{path.resolve()}` not found")
    if not path.is_file():
        raise ParseTomlFileAsModelError(error=f"`{path.resolve()}` is not a file")

    file_content = path.read_text()
    try:
        parsed_toml: dict[str, object] = tomllib.loads(file_content)
    except tomllib.TOMLDecodeError as error:
        raise ParseTomlFileAsModelError(
            error=f"Toml decode error occurred when parsing `{path}`"
        ) from error

    try:
        return model_type.model_validate(parsed_toml)
    except pydantic.ValidationError as error:
        raise ParseTomlFileAsModelError(
            error=f"Error when parsing decoded toml dict from file `{path}`"
        ) from error


def get_strictql_queries_to_generate(
    parsed_queries_to_generate_by_query_file_path: dict[
        pathlib.Path, dict[str, ParsedQueryToGenerate]
    ],
    code_generated_dir: str,
    parsed_databases: dict[str, ParsedDatabase],
    environment_variables: Mapping[str, str],
) -> StrictQLQueriesToGenerate:
    databases: dict[str, DataBaseSettings] = {}
    for database_name, database_settings in parsed_databases.items():
        if (
            database_settings.env_name_to_read_connection_url
            not in environment_variables
        ):
            raise GetStrictQLQueriesToGenerateError(
                error=f"Environment variable `{database_settings.env_name_to_read_connection_url}` with connection url to database: `{database_name}` not set"
            )

        databases[database_name] = DataBaseSettings(
            connection_url=SecretStr(
                environment_variables[database_settings.env_name_to_read_connection_url]
            )
        )

    code_generation_dir_path = pathlib.Path(code_generated_dir).resolve()

    queries_to_generate_with_source_info_by_file_path: dict[
        pathlib.Path, list[QueryToGenerateWithSourceInfo]
    ] = defaultdict(list)
    for (
        query_file_path,
        parsed_queries_to_generate,
    ) in parsed_queries_to_generate_by_query_file_path.items():
        for query_name, query_to_generate in parsed_queries_to_generate.items():
            for special_path_symbol in ["~", "..", "."]:
                if special_path_symbol in str(query_to_generate.relative_path).split(
                    "/"
                ):
                    raise GetStrictQLQueriesToGenerateError(
                        error=f"Found special path symbol: `{special_path_symbol}` in a query to generate path: `{query_to_generate.relative_path}`, query_file: `{code_generation_dir_path / query_file_path}`"
                    )
            if query_to_generate.database not in databases:
                raise GetStrictQLQueriesToGenerateError(
                    error=f"Database : `{query_to_generate.database}` in a query: `{query_file_path}::{query_name}` not exists in a strictql settings"
                )
            try:
                function_name = StringInSnakeLowerCase(value=query_name)
            except StringNotInLowerSnakeCase as error:
                raise GetStrictQLQueriesToGenerateError(
                    error=f"Query name not in lower case snake string, query identifier: `{query_file_path.resolve()}::{query_name}`"
                ) from error

            queries_to_generate_with_source_info_by_file_path[
                code_generation_dir_path / query_to_generate.relative_path
            ].append(
                QueryToGenerateWithSourceInfo(
                    query_to_generate=QueryToGenerate(
                        query=query_to_generate.query,
                        function_name=function_name,
                        parameters={
                            key: Parameter(is_optional=value.is_optional)
                            for key, value in query_to_generate.parameter_names.items()
                        },
                        query_type=query_to_generate.query_type,
                        database_name=query_to_generate.database,
                        database_connection_url=databases[
                            query_to_generate.database
                        ].connection_url,
                    ),
                    query_file_path=query_file_path,
                    query_name=query_name,
                )
            )

    queries_to_generate_by_target_path = {}
    for (
        query_to_generate_path,
        queries_to_generate,
    ) in queries_to_generate_with_source_info_by_file_path.items():
        if len(queries_to_generate) != 1:
            queries_identifiers = [
                f"{query.query_file_path.resolve()}::{query.query_name}"
                for query in queries_to_generate
            ]
            raise GetStrictQLQueriesToGenerateError(
                error=f"Found multiple queries to generate with path: `{(code_generation_dir_path / query_to_generate_path).resolve()}`, queries: {queries_identifiers}"
            )

        queries_to_generate_by_target_path[query_to_generate_path] = (
            queries_to_generate[0].query_to_generate
        )

    return StrictQLQueriesToGenerate(
        queries_to_generate=queries_to_generate_by_target_path,
        generated_code_path=pathlib.Path(code_generated_dir),
        databases=databases,
    )
