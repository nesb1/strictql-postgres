import dataclasses
import pathlib
from typing import Literal

import pydantic

from strictql_postgres.queries_to_generate import StrictQLQuiriesToGenerate


class PyprojectTomlModel(pydantic.BaseModel):
    tools: dict[str, object]


def parse_pyproject_toml(path: pathlib.Path) -> PyprojectTomlModel:
    pass


class ParsedDatabase(pydantic.BaseModel):  # type: ignore[explicit-any,misc]
    env_name_to_read_connection_url: str


class ParsedStrictqlSettings(pydantic.BaseModel):  # type: ignore[explicit-any,misc]
    query_files_path: list[str]
    code_generate_dir: str
    databases: dict[str, ParsedDatabase]


def parse_strictql_settings_from_pyproject_toml(
    parsed_pyproject_toml: PyprojectTomlModel,
) -> ParsedStrictqlSettings:
    pass


class ParsedParameter(pydantic.BaseModel):  # type: ignore[explicit-any,misc]
    is_optional: bool


class ParsedQueryToGenerate(pydantic.BaseModel):  # type: ignore[explicit-any,misc]
    query: str
    parameter_names: dict[str, ParsedParameter] = {}
    database: str
    return_type: Literal["list"]
    relative_path: str


def parse_query_file(path: pathlib.Path) -> ParsedQueryToGenerate:
    pass


@dataclasses.dataclass(frozen=True)
class DataClassError(Exception):
    error: str

    def __str__(self) -> str:
        return self.error


class GetStrictQLQueriesToGenerateError(DataClassError):
    pass


def get_strictql_queries_to_generate(
    parsed_queries_to_generate: dict[pathlib.Path, list[ParsedQueryToGenerate]],
    code_generated_dir: str,
    databases: dict[str, ParsedDatabase],
    environment_variables: dict[str, str],
) -> StrictQLQuiriesToGenerate:
    unique_file_paths = set()
    queries_to_generate = []
    for (
        query_file_path,
        parsed_queries_to_generate,
    ) in parsed_queries_to_generate.items():
        for query_to_generate in parsed_queries_to_generate:
            for special_path_symbol in ["~", "..", "."]:
                if special_path_symbol in str(query_to_generate.relative_path).split(
                    "/"
                ):
                    raise GetStrictQLQueriesToGenerateError(
                        error=f"Found special path symbol: `{special_path_symbol}` in a query to generate path: `{query_to_generate.relative_path}`, query_file: `{query_file_path}`"
                    )
            if query_to_generate.relative_path in unique_file_paths:
                raise GetStrictQLQueriesToGenerateError(
                    error=f"Found not unique path for query generation, file_path: `{query_to_generate.relative_path}`"
                )

        pass
