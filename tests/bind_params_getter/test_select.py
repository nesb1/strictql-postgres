import dataclasses

import pytest

import asyncpg
from strictql_postgres.pg_bind_params_type_getter import (
    get_bind_params_python_types,
)
from strictql_postgres.python_types import SimpleType, SimpleTypes
from strictql_postgres.supported_postgres_types import SupportedPostgresSimpleTypes


@dataclasses.dataclass
class SimpleTypeTestData:
    bind_param_cast: str
    expected_python_type: SimpleTypes


TEST_DATA_FOR_SIMPLE_TYPES: dict[SupportedPostgresSimpleTypes, SimpleTypeTestData] = {
    SupportedPostgresSimpleTypes.SMALLINT: SimpleTypeTestData(
        bind_param_cast="smallint",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.INTEGER: SimpleTypeTestData(
        bind_param_cast="integer",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.BIGINT: SimpleTypeTestData(
        bind_param_cast="bigint",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.REAL: SimpleTypeTestData(
        bind_param_cast="real",
        expected_python_type=SimpleTypes.FLOAT,
    ),
    SupportedPostgresSimpleTypes.DOUBLE_PRECISION: SimpleTypeTestData(
        bind_param_cast="double precision",
        expected_python_type=SimpleTypes.FLOAT,
    ),
    SupportedPostgresSimpleTypes.VARCHAR: SimpleTypeTestData(
        bind_param_cast="varchar", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.CHAR: SimpleTypeTestData(
        bind_param_cast="char", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.BPCHAR: SimpleTypeTestData(
        bind_param_cast="bpchar", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.TEXT: SimpleTypeTestData(
        bind_param_cast="text", expected_python_type=SimpleTypes.STR
    ),
}


@pytest.mark.parametrize(
    ("query_literal", "expected_python_type"),
    [
        (test_case.bind_param_cast, test_case.expected_python_type)
        for postgres_type, test_case in TEST_DATA_FOR_SIMPLE_TYPES.items()
    ],
)
async def test_get_bind_params_types_for_simple_types(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_type: SimpleTypes,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(
            f"select ($1::{query_literal}) as value"
        )
        actual_bind_params = await get_bind_params_python_types(
            prepared_statement=prepared_statement,
        )

        assert actual_bind_params == [
            SimpleType(type_=expected_python_type, is_optional=True)
        ]
