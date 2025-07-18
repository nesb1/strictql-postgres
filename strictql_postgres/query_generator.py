import dataclasses
import typing
from typing import Literal, assert_never

from pydantic import BaseModel

import asyncpg
from asyncpg.exceptions import PostgresError
from strictql_postgres.code_generator import (
    generate_code_for_query_with_execute_method,
    generate_code_for_query_with_fetch_all_method,
    generate_code_for_query_with_fetch_row_method,
)
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.common_types import BindParam, NotEmptyRowSchema
from strictql_postgres.format_exception import format_exception
from strictql_postgres.pg_bind_params_type_getter import get_bind_params_python_types
from strictql_postgres.pg_response_schema_getter import (
    PgResponseSchemaContainsColumnsWithInvalidNames,
    PgResponseSchemaContainsColumnsWithNotUniqueNames,
    PgResponseSchemaGetterError,
    PgResponseSchemaTypeNotSupported,
    get_pg_response_schema_from_prepared_statement,
)
from strictql_postgres.queries_to_generate import Parameter
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase

TYPES_MAPPING = {"int4": int, "varchar": str, "text": str}


@dataclasses.dataclass()
class QueryPythonCodeGeneratorError(Exception):
    error: str


@dataclasses.dataclass
class InvalidParamNames(QueryPythonCodeGeneratorError):
    query: str
    expected_param_names_count: int
    actual_params: dict[str, Parameter]

    def __str__(self) -> str:
        return f"""{{
query: {self.query},
expected_param_names_count: {self.expected_param_names_count},
actual_param_names: {self.actual_params}
}}"""


class QueryToGenerateInfo(BaseModel):  # type: ignore[explicit-any]
    query: str
    function_name: StringInSnakeLowerCase
    params: dict[str, Parameter]
    query_type: Literal["fetch", "execute", "fetch_row"]


async def generate_query_python_code(
    query_to_generate: QueryToGenerateInfo, connection_pool: asyncpg.Pool
) -> str:
    async with connection_pool.acquire() as connection:
        try:
            prepared_statement = await connection.prepare(query=query_to_generate.query)
        except PostgresError as error:
            raise QueryPythonCodeGeneratorError(
                error=f"Invalid SQL query: {query_to_generate.query}, postgres_error: {format_exception(error)}"
            )

        try:
            schema = get_pg_response_schema_from_prepared_statement(
                prepared_stmt=prepared_statement,
            )
        except PgResponseSchemaGetterError as schema_getter_error:
            match schema_getter_error.error:
                case PgResponseSchemaTypeNotSupported():
                    raise QueryPythonCodeGeneratorError(
                        error=f"Postgres type: `{schema_getter_error.error.postgres_type}` in column: `{schema_getter_error.error.column_name}` not supported yet"
                    )
                case PgResponseSchemaContainsColumnsWithInvalidNames():
                    raise QueryPythonCodeGeneratorError(
                        error=f"Invalid column names exists in response schema, column names: `{schema_getter_error.error.invalid_column_names}`"
                    )
                case PgResponseSchemaContainsColumnsWithNotUniqueNames():
                    raise QueryPythonCodeGeneratorError(
                        error=f"Column names in response schema not unique, column_names {schema_getter_error.error.not_unique_column_names}"
                    )
                case _:
                    typing.assert_never(schema_getter_error.error)

        pg_param_types = await get_bind_params_python_types(
            prepared_statement=prepared_statement,
        )

        if len(pg_param_types) != len(query_to_generate.params):
            raise QueryPythonCodeGeneratorError(
                error=f"Query contains invalid param names count, expected param names count: `{len(pg_param_types)}`, actual_params_count: `{len(query_to_generate.params)}`"
            )

        params = []
        if query_to_generate.params:
            for parameter_from_pg, (user_parameter_name, user_parameter) in zip(
                pg_param_types, query_to_generate.params.items()
            ):
                parameter_from_pg.is_optional = user_parameter.is_optional
                params.append(
                    BindParam(
                        name_in_function=user_parameter_name,
                        type_=parameter_from_pg,
                    )
                )
    improver = CodeFixer()
    match query_to_generate.query_type:
        case "fetch":
            return await generate_code_for_query_with_fetch_all_method(
                query=query_to_generate.query,
                result_schema=NotEmptyRowSchema(schema=schema),
                bind_params=params,
                function_name=query_to_generate.function_name,
                code_quality_improver=improver,
            )
        case "execute":
            return await generate_code_for_query_with_execute_method(
                query=query_to_generate.query,
                bind_params=params,
                function_name=query_to_generate.function_name,
                code_quality_improver=improver,
            )
        case "fetch_row":
            return await generate_code_for_query_with_fetch_row_method(
                query=query_to_generate.query,
                result_schema=NotEmptyRowSchema(schema=schema),
                bind_params=params,
                function_name=query_to_generate.function_name,
                code_quality_improver=improver,
            )

        case "_":
            assert_never(query_to_generate.query_type)
