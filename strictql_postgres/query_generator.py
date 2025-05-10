import dataclasses
import pathlib
from typing import Literal

from pydantic import BaseModel

import asyncpg
from asyncpg.exceptions import PostgresSyntaxError
from strictql_postgres.code_generator import (
    generate_code_for_query_with_execute_method,
    generate_code_for_query_with_fetch_all_method,
)
from strictql_postgres.code_quality import CodeQualityImprover, MypyRunner
from strictql_postgres.common_types import BindParam, NotEmptyRowSchema
from strictql_postgres.pg_bind_params_type_getter import get_bind_params_python_types
from strictql_postgres.pg_response_schema_getter import (
    PgResponseSchemaContainsColumnsWithInvalidNames,
    PgResponseSchemaContainsColumnsWithNotUniqueNames,
    PgResponseSchemaGetterError,
    PgResponseSchemaTypeNotSupported,
    get_pg_response_schema_from_prepared_statement,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase

TYPES_MAPPING = {"int4": int, "varchar": str, "text": str}


class QueryPythonCodeGeneratorError(Exception):
    pass


@dataclasses.dataclass
class InvalidResponseSchemaError(QueryPythonCodeGeneratorError):
    error: (
        PgResponseSchemaContainsColumnsWithNotUniqueNames
        | PgResponseSchemaContainsColumnsWithInvalidNames
        | PgResponseSchemaTypeNotSupported
    )

    def __str__(self) -> str:
        return f"Invalid response schema: {self.error}"


@dataclasses.dataclass
class InvalidSqlQuery(QueryPythonCodeGeneratorError):
    query: str
    postgres_error: str


@dataclasses.dataclass
class InvalidParamNames(QueryPythonCodeGeneratorError):
    query: str
    expected_param_names_count: int
    actual_param_names: list[str]

    def __str__(self) -> str:
        return f"""{{
query: {self.query},
expected_param_names_count: {self.expected_param_names_count},
actual_param_names: {self.actual_param_names}
}}"""


class QueryToGenerate(BaseModel):  # type: ignore[explicit-any,misc]
    query: str
    function_name: str
    param_names: list[str]
    return_type: Literal["list", "execute"]


async def generate_query_python_code(
    query_to_generate: QueryToGenerate, connection_pool: asyncpg.Pool
) -> str:
    async with connection_pool.acquire() as connection:
        try:
            prepared_statement = await connection.prepare(query=query_to_generate.query)
        except PostgresSyntaxError as error:
            raise InvalidSqlQuery(
                query=query_to_generate.query, postgres_error=error.message
            ) from error

        try:
            schema = get_pg_response_schema_from_prepared_statement(
                prepared_stmt=prepared_statement,
            )
        except PgResponseSchemaGetterError as schema_getter_error:
            raise InvalidResponseSchemaError(error=schema_getter_error.error)

        param_types = await get_bind_params_python_types(
            prepared_statement=prepared_statement,
        )

        if len(param_types) != len(query_to_generate.param_names):
            raise InvalidParamNames(
                query=query_to_generate.query,
                expected_param_names_count=len(param_types),
                actual_param_names=query_to_generate.param_names,
            )
        params = []
        if query_to_generate.param_names:
            for index, parameter_type in enumerate(param_types):
                params.append(
                    BindParam(
                        name_in_function=query_to_generate.param_names[index],
                        type_=parameter_type,
                    )
                )
    improver = CodeQualityImprover(mypy_runner=MypyRunner(mypy_path=pathlib.Path.cwd()))
    match query_to_generate.return_type:
        case "list":
            return await generate_code_for_query_with_fetch_all_method(
                query=query_to_generate.query,
                result_schema=NotEmptyRowSchema(schema=schema),
                bind_params=params,
                function_name=StringInSnakeLowerCase(query_to_generate.function_name),
                code_quality_improver=improver,
            )
        case "execute":
            return await generate_code_for_query_with_execute_method(
                query=query_to_generate.query,
                bind_params=params,
                function_name=StringInSnakeLowerCase(query_to_generate.function_name),
                code_quality_improver=improver,
            )

        case "_":
            raise NotImplementedError()
