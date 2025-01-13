import dataclasses
import decimal
import types

import pydantic
import pytest

import asyncpg
from strictql_postgres.code_generator import (
    generate_code_for_query_with_fetch_all_method,
)
from strictql_postgres.code_quality import CodeQualityImprover
from strictql_postgres.common_types import NotEmptyRowSchema
from strictql_postgres.pg_response_schema_getter import (
    get_pg_response_schema_from_prepared_statement,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.supported_postgres_types import (
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)


@dataclasses.dataclass
class TypeTestData:
    query_literal: str
    expected_python_value: object


TEST_DATA_FOR_SIMPLE_TYPES: dict[SupportedPostgresSimpleTypes, TypeTestData] = {
    SupportedPostgresSimpleTypes.SMALLINT: TypeTestData(
        query_literal="(1::smallint)",
        expected_python_value=1,
    ),
    SupportedPostgresSimpleTypes.INTEGER: TypeTestData(
        query_literal="(1::integer)",
        expected_python_value=1,
    ),
    SupportedPostgresSimpleTypes.BIGINT: TypeTestData(
        query_literal="(1::bigint)",
        expected_python_value=1,
    ),
    SupportedPostgresSimpleTypes.REAL: TypeTestData(
        query_literal="(123::real)",
        expected_python_value=float(123),
    ),
    SupportedPostgresSimpleTypes.DOUBLE_PRECISION: TypeTestData(
        query_literal="(123.1::double precision)",
        expected_python_value=123.1,
    ),
    SupportedPostgresSimpleTypes.VARCHAR: TypeTestData(
        query_literal="('text'::varchar)",
        expected_python_value="text",
    ),
    SupportedPostgresSimpleTypes.CHAR: TypeTestData(
        query_literal="('text'::char(5))", expected_python_value="text "
    ),
    SupportedPostgresSimpleTypes.BPCHAR: TypeTestData(
        query_literal="('text'::bpchar)", expected_python_value="text"
    ),
    SupportedPostgresSimpleTypes.TEXT: TypeTestData(
        query_literal="('text'::text)", expected_python_value="text"
    ),
}


@pytest.mark.parametrize(
    ("query_literal", "expected_python_value"),
    [
        (
            TEST_DATA_FOR_SIMPLE_TYPES[data_type].query_literal,
            TEST_DATA_FOR_SIMPLE_TYPES[data_type].expected_python_value,
        )
        for data_type in SupportedPostgresSimpleTypes
    ],
)
async def test_generate_code_and_execute_for_simple_types_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_value: object,
    code_quality_improver: CodeQualityImprover,
) -> None:
    query = f"select {query_literal} as value"
    function_name = "fetch_all_test"

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(query)

        response_schema = get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt
        )

        code = await generate_code_for_query_with_fetch_all_method(
            query=query,
            result_schema=NotEmptyRowSchema(schema=response_schema),
            bind_params=[],
            function_name=StringInSnakeLowerCase(function_name),
            code_quality_improver=code_quality_improver,
        )

        generated_module = types.ModuleType("generated_module")

        exec(code, generated_module.__dict__)  # type: ignore[misc]

        res = await generated_module.fetch_all_test(connection)  # type: ignore[misc]

        assert res[0].value == expected_python_value  # type: ignore[misc]

        model: pydantic.BaseModel = generated_module.FetchAllTestModel
        assert (
            model.model_fields["value"].annotation == type(expected_python_value) | None  # type: ignore[misc]
        )


TEST_DATA_FOR_TYPES_WITH_IMPORT: dict[
    SupportedPostgresTypeRequiredImports, TypeTestData
] = {
    SupportedPostgresTypeRequiredImports.NUMERIC: TypeTestData(
        query_literal="('1.012'::numeric)",
        expected_python_value=decimal.Decimal("1.012"),
    ),
    SupportedPostgresTypeRequiredImports.DECIMAL: TypeTestData(
        query_literal="('1.012'::numeric)",
        expected_python_value=decimal.Decimal("1.012"),
    ),
}


@pytest.mark.parametrize(
    ("query_literal", "expected_python_value"),
    [
        (
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].query_literal,
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].expected_python_value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
    ],
)
async def test_generate_code_and_execute_for_types_with_import_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_value: object,
    code_quality_improver: CodeQualityImprover,
) -> None:
    query = f"select {query_literal} as value"
    function_name = "fetch_all_test"

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(query)

        response_schema = get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt
        )

        code = await generate_code_for_query_with_fetch_all_method(
            query=query,
            result_schema=NotEmptyRowSchema(schema=response_schema),
            bind_params=[],
            function_name=StringInSnakeLowerCase(function_name),
            code_quality_improver=code_quality_improver,
        )

        generated_module = types.ModuleType("generated_module")

        exec(code, generated_module.__dict__)  # type: ignore[misc]

        res = await generated_module.fetch_all_test(connection)  # type: ignore[misc]

        assert res[0].value == expected_python_value  # type: ignore[misc]

        model: pydantic.BaseModel = generated_module.FetchAllTestModel
        assert (
            model.model_fields["value"].annotation == type(expected_python_value) | None  # type: ignore[misc]
        )
