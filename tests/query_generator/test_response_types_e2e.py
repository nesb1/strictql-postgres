import dataclasses
import datetime
import decimal
import types

import pydantic
import pytest

import asyncpg
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.query_generator import (
    QueryToGenerate,
    generate_query_python_code,
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
    code_quality_improver: CodeFixer,
) -> None:
    query = f"select {query_literal} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerate(
            query=query,
            params={},
            query_type="fetch",
            function_name=StringInSnakeLowerCase(function_name),
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
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
        query_literal="('1.012'::decimal)",
        expected_python_value=decimal.Decimal("1.012"),
    ),
    SupportedPostgresTypeRequiredImports.DATE: TypeTestData(
        query_literal="('2020-07-09'::date)",
        expected_python_value=datetime.date(year=2020, month=7, day=9),
    ),
    SupportedPostgresTypeRequiredImports.TIME: TypeTestData(
        query_literal="('09:08:00'::time without time zone)",
        expected_python_value=datetime.time(hour=9, minute=8, second=0),
    ),
    SupportedPostgresTypeRequiredImports.TIMETZ: TypeTestData(
        query_literal="('09:08:00'::time with time zone)",
        expected_python_value=datetime.time(
            hour=9, minute=8, second=0, tzinfo=datetime.timezone.utc
        ),
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMPTZ: TypeTestData(
        query_literal="('2020-07-09T09:08:00'::timestamp with time zone)",
        expected_python_value=datetime.datetime(
            year=2020,
            month=7,
            day=9,
            hour=9,
            minute=8,
            second=0,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMP: TypeTestData(
        query_literal="('2020-07-09T09:08:00'::timestamp without time zone)",
        expected_python_value=datetime.datetime(
            year=2020,
            month=7,
            day=9,
            hour=9,
            minute=8,
            second=0,
        ),
    ),
    SupportedPostgresTypeRequiredImports.INTERVAL: TypeTestData(
        query_literal="('1 year'::interval)",
        expected_python_value=datetime.timedelta(days=365),
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
    code_quality_improver: CodeFixer,
) -> None:
    query = f"select {query_literal} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerate(
            query=query,
            function_name=StringInSnakeLowerCase(function_name),
            params={},
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection)  # type: ignore[misc]

        assert res[0].value == expected_python_value  # type: ignore[misc]

    model: pydantic.BaseModel = generated_module.FetchAllTestModel
    assert (
        model.model_fields["value"].annotation == type(expected_python_value) | None  # type: ignore[misc]
    )
