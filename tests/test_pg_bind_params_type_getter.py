import asyncpg
import pytest

from strictql_postgres.pg_bind_params_type_getter import (
    get_bind_params_python_types_from_prepared_statement,
    QueryParamType,
    PgBindParamTypeNotSupportedError,
)


@pytest.mark.parametrize(
    ("query", "expected_params"),
    [
        ("select 1", []),
        ("select * from (values (1)) as v (a) where a = $1;", [int]),
        (
            "select * from (values (1,'kek')) as v (a,b) where a = $1 and b = $2;",
            [int, str],
        ),
    ],
)
async def test_get_bind_params_types_for_query(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    expected_params: list[QueryParamType],
) -> None:
    python_type_by_postgres_type = {
        "int4": int,
        "varchar": str,
        "text": str,
    }

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(query)
        assert expected_params == get_bind_params_python_types_from_prepared_statement(
            prepared_statement=prepared_statement,
            python_type_by_postgres_type=python_type_by_postgres_type,
        )


async def test_get_bind_params_types_for_query_with_params_when_not_supported_type(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare("select $1")
        with pytest.raises(PgBindParamTypeNotSupportedError) as error:
            get_bind_params_python_types_from_prepared_statement(
                prepared_statement=prepared_statement, python_type_by_postgres_type={}
            )
        assert error.value.postgres_type == "text"
