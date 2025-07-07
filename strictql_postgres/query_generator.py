import dataclasses
from typing import Literal

from pydantic import BaseModel

import asyncpg
from asyncpg.exceptions import PostgresSyntaxError
from strictql_postgres.code_generator import (
    generate_code_for_query_with_execute_method,
    generate_code_for_query_with_fetch_all_method,
    generate_code_for_query_with_fetch_row_method,
)
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.common_types import BindParam, NotEmptyRowSchema
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
    actual_params: dict[str, Parameter]

    def __str__(self) -> str:
        return f"""{{
query: {self.query},
expected_param_names_count: {self.expected_param_names_count},
actual_param_names: {self.actual_params}
}}"""


class QueryToGenerate(BaseModel):  # type: ignore[explicit-any]
    query: str
    function_name: StringInSnakeLowerCase
    params: dict[str, Parameter]
    query_type: Literal["fetch", "execute", "fetch_row"]


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

        pg_param_types = await get_bind_params_python_types(
            prepared_statement=prepared_statement,
        )

        if len(pg_param_types) != len(query_to_generate.params):
            raise InvalidParamNames(
                query=query_to_generate.query,
                expected_param_names_count=len(pg_param_types),
                actual_params=query_to_generate.params,
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
            raise NotImplementedError()
