import pytest

import asyncpg
from strictql_postgres.pg_response_schema_getter import (
    PgResponseSchemaContainsColumnsWithInvalidNames,
    PgResponseSchemaContainsColumnsWithNotUniqueNames,
    PgResponseSchemaGetterError,
    get_pg_response_schema_from_prepared_statement,
)
from strictql_postgres.python_types import (
    RecursiveListSupportedTypes,
    RecursiveListType,
    SimpleTypes,
    TypesWithImport,
)
from strictql_postgres.supported_postgres_types import (
    ALL_SUPPORTED_POSTGRES_TYPES,
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)
from tests.pg_types_test_data import (
    TEST_DATA_FOR_ALL_TYPES,
    TEST_DATA_FOR_SIMPLE_TYPES,
    TEST_DATA_FOR_TYPES_WITH_IMPORT,
    SimpleTypeTestData,
)


@pytest.mark.parametrize(
    ("postgres_value", "cast_str", "expected_python_type"),
    [
        (
            test_data.test_data.postgres_value_as_str,
            test_data.test_data.cast_str,
            test_data.simple_type(is_optional=True),
        )
        for simple_type in SupportedPostgresSimpleTypes
        for test_data in TEST_DATA_FOR_SIMPLE_TYPES[simple_type]
    ],
)
async def test_get_pg_response_schema_from_prepared_statement_when_simple_type(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    postgres_value: str,
    cast_str: str,
    expected_python_type: SimpleTypes,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(
            query=f"select ({postgres_value})::{cast_str} as value"
        )
        assert get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt,
        ) == {
            "value": expected_python_type,
        }


@pytest.mark.parametrize(
    ("query_literal", "expected_python_type"),
    [
        (
            f"({test_data.test_data.postgres_value_as_str})::{test_data.test_data.cast_str}",
            test_data.type_with_import(is_optional=True),
        )
        for type_ in SupportedPostgresTypeRequiredImports
        for test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[type_]
    ],
)
async def test_get_pg_response_schema_from_prepared_statement_when_type_required_import(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_type: TypesWithImport,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(
            query=f"select {query_literal} as value"
        )
        assert get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt,
        ) == {
            "value": expected_python_type,
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


class Model:
    v: list[int] | list[list[int]]


@pytest.mark.parametrize("array_dimension", [1, 3, 10])
@pytest.mark.parametrize(
    ("query_literal", "expected_python_type"),
    [
        (
            f"({test_data.test_data.postgres_value_as_str})::{test_data.test_data.cast_str}",
            (
                test_data.simple_type(is_optional=True)
                if isinstance(test_data, SimpleTypeTestData)
                else test_data.type_with_import(is_optional=True)
            ),
        )
        for type_ in ALL_SUPPORTED_POSTGRES_TYPES
        for test_data in TEST_DATA_FOR_ALL_TYPES[type_]
    ],
)
async def test_array(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    array_dimension: int,
    expected_python_type: RecursiveListSupportedTypes,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        start = "".join(["ARRAY[" for _ in range(array_dimension)])

        end = "".join(["]" for _ in range(array_dimension)])
        prepared_stmt = await connection.prepare(
            f"select {start}{query_literal}{end} as value"
        )

        pg_response_schema = get_pg_response_schema_from_prepared_statement(
            prepared_stmt=prepared_stmt
        )

        assert pg_response_schema == {
            "value": RecursiveListType(
                generic_type=expected_python_type, is_optional=True
            )
        }
