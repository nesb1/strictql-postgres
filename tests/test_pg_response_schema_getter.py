import dataclasses

import pytest

import asyncpg
from strictql_postgres.pg_response_schema_getter import (
    PgResponseSchemaContainsColumnsWithInvalidNames,
    PgResponseSchemaContainsColumnsWithNotUniqueNames,
    PgResponseSchemaGetterError,
    get_pg_response_schema_from_prepared_statement,
)
from strictql_postgres.python_types import (
    DateTimeType,
    DateType,
    DecimalType,
    SimpleType,
    SimpleTypes,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
)
from strictql_postgres.supported_postgres_types import (
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)


@dataclasses.dataclass
class SimpleTypeTestData:
    query_literal: str
    expected_python_type: SimpleTypes


TEST_DATA_FOR_SIMPLE_TYPES: dict[SupportedPostgresSimpleTypes, SimpleTypeTestData] = {
    SupportedPostgresSimpleTypes.SMALLINT: SimpleTypeTestData(
        query_literal="(1::smallint)",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.INTEGER: SimpleTypeTestData(
        query_literal="(1::integer)",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.BIGINT: SimpleTypeTestData(
        query_literal="(1::bigint)",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.REAL: SimpleTypeTestData(
        query_literal="(1::real)",
        expected_python_type=SimpleTypes.FLOAT,
    ),
    SupportedPostgresSimpleTypes.DOUBLE_PRECISION: SimpleTypeTestData(
        query_literal="(123::double precision)",
        expected_python_type=SimpleTypes.FLOAT,
    ),
    SupportedPostgresSimpleTypes.VARCHAR: SimpleTypeTestData(
        query_literal="('text'::varchar)", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.CHAR: SimpleTypeTestData(
        query_literal="('text'::char)", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.BPCHAR: SimpleTypeTestData(
        query_literal="('text'::bpchar)", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.TEXT: SimpleTypeTestData(
        query_literal="('text'::text)", expected_python_type=SimpleTypes.STR
    ),
}


@pytest.mark.parametrize(
    ("query_literal", "expected_python_type"),
    [
        (
            TEST_DATA_FOR_SIMPLE_TYPES[simple_type].query_literal,
            TEST_DATA_FOR_SIMPLE_TYPES[simple_type].expected_python_type,
        )
        for simple_type in SupportedPostgresSimpleTypes
    ],
)
async def test_get_pg_response_schema_from_prepared_statement_when_simple_type(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_type: SimpleTypes,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(
            query=f"select {query_literal} as value"
        )
        assert get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt,
        ) == {
            "value": SimpleType(type_=expected_python_type, is_optional=True),
        }


@dataclasses.dataclass
class TypeRequiredImportTestData:
    query_literal: str
    expected_python_type: type[TypesWithImport]


TEST_DATA_FOR_TYPES_REQUIRED_IMPORT: dict[
    SupportedPostgresTypeRequiredImports, TypeRequiredImportTestData
] = {
    SupportedPostgresTypeRequiredImports.NUMERIC: TypeRequiredImportTestData(
        query_literal="(123::numeric)",
        expected_python_type=DecimalType,
    ),
    SupportedPostgresTypeRequiredImports.DECIMAL: TypeRequiredImportTestData(
        query_literal="(123::decimal)",
        expected_python_type=DecimalType,
    ),
    SupportedPostgresTypeRequiredImports.DATE: TypeRequiredImportTestData(
        query_literal="(now()::date)",
        expected_python_type=DateType,
    ),
    SupportedPostgresTypeRequiredImports.TIME: TypeRequiredImportTestData(
        query_literal="(now()::time)",
        expected_python_type=TimeType,
    ),
    SupportedPostgresTypeRequiredImports.TIMETZ: TypeRequiredImportTestData(
        query_literal="(now()::timetz)",
        expected_python_type=TimeType,
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMP: TypeRequiredImportTestData(
        query_literal="(now()::timestamp without time zone)",
        expected_python_type=DateTimeType,
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMPTZ: TypeRequiredImportTestData(
        query_literal="(now()::timestamp with time zone)",
        expected_python_type=DateTimeType,
    ),
    SupportedPostgresTypeRequiredImports.INTERVAL: TypeRequiredImportTestData(
        query_literal="('1 year'::interval)",
        expected_python_type=TimeDeltaType,
    ),
}


@pytest.mark.parametrize(
    ("query_literal", "expected_python_type"),
    [
        (
            TEST_DATA_FOR_TYPES_REQUIRED_IMPORT[type_].query_literal,
            TEST_DATA_FOR_TYPES_REQUIRED_IMPORT[type_].expected_python_type,
        )
        for type_ in SupportedPostgresTypeRequiredImports
    ],
)
async def test_get_pg_response_schema_from_prepared_statement_when_type_required_import(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_type: type[TypesWithImport],
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(
            query=f"select {query_literal} as value"
        )
        assert get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt,
        ) == {
            "value": expected_python_type(is_optional=True),
        }


@pytest.mark.parametrize(
    ("query", "column_names", "invalid_column_names"),
    [
        ("select 1, 2", ["?column?", "?column?"], ["?column?", "?column?"]),
        ("select 1 as def", ["def"], ["def"]),
        ("select 1 as as", ["as"], ["as"]),
    ],
)
async def test_raise_error_if_response_schema_contains_invalid_columns(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    column_names: list[str],
    invalid_column_names: list[str],
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(query=query)
        with pytest.raises(PgResponseSchemaGetterError) as error:
            get_pg_response_schema_from_prepared_statement(
                prepared_stmt=prepared_stmt,
            )

        assert error.value.error == PgResponseSchemaContainsColumnsWithInvalidNames(
            column_names=column_names,
            invalid_column_names=invalid_column_names,
        )


async def test_raise_error_if_response_schema_contains_not_unique_columns(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(query="select 1 as value, 2 as value")
        with pytest.raises(PgResponseSchemaGetterError) as error:
            get_pg_response_schema_from_prepared_statement(
                prepared_stmt=prepared_stmt,
            )
        assert error.value.error == PgResponseSchemaContainsColumnsWithNotUniqueNames(
            column_names=["value", "value"], not_unique_column_names={"value"}
        )
