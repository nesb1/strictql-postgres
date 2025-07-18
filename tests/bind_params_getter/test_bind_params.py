import pytest

import asyncpg
from strictql_postgres.pg_bind_params_type_getter import (
    get_bind_params_python_types,
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
    ("query_literal", "expected_simple_type"),
    [
        (test_data.test_data.cast_str, test_data.simple_type)
        for supported_type in SupportedPostgresSimpleTypes
        for test_data in TEST_DATA_FOR_SIMPLE_TYPES[supported_type]
    ],
)
async def test_get_bind_params_types_for_simple_types(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_simple_type: type[SimpleTypes],
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(
            f"select ($1::{query_literal}) as value"
        )
        actual_bind_params = await get_bind_params_python_types(
            prepared_statement=prepared_statement,
        )

        assert actual_bind_params == [expected_simple_type(is_optional=True)]


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            test_data.test_data.cast_str,
            test_data.type_with_import,
        )
        for data_type in SupportedPostgresTypeRequiredImports
        for test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type]
    ],
)
async def test_bind_params_for_types_with_import(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    bind_param_cast: str,
    param: type[TypesWithImport],
) -> None:
    query = f"select ($1::{bind_param_cast}) as value"

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(query)

        actual_bind_params = await get_bind_params_python_types(
            prepared_statement=prepared_statement
        )

        assert actual_bind_params == [param(is_optional=True)]


@pytest.mark.parametrize("array_dimension", [1, 3, 10])
@pytest.mark.parametrize(
    ("cast_", "expected_python_type"),
    [
        (
            test_data.test_data.cast_str,
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
    cast_: str,
    array_dimension: int,
    expected_python_type: RecursiveListSupportedTypes,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        array_cast_str = "".join(["[]" for _ in range(array_dimension)])
        prepared_stmt = await connection.prepare(
            f"select $1::{cast_}{array_cast_str} as value"
        )

        actual_bind_params = await get_bind_params_python_types(
            prepared_statement=prepared_stmt
        )

        assert actual_bind_params == [
            RecursiveListType(generic_type=expected_python_type, is_optional=True)
        ]
