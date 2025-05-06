import asyncpg
import pytest

from strictql_postgres.pg_bind_params_type_getter import (
    BindParamType,
    get_bind_params_python_types,
)


@pytest.mark.parametrize(
    ("query", "expected_params"),
    [
        ("select 1", []),
        ("select 1", []),
        (
            "select * from (values (1)) as v (a) where a = $1;",
            [BindParamType(int, is_optional=True)],
        ),
        (
            "select * from (values (1)) as v (a) where a = $1;",
            [BindParamType(int, is_optional=True)],
        ),
        (
            "select * from (values (1,'kek')) as v (a,b) where a = $1 and b = $2;",
            [
                BindParamType(int, is_optional=True),
                BindParamType(str, is_optional=True),
            ],
        ),
        (
            "select * from (values (1,'kek')) as v (a,b) where a = $1 and b = $2;",
            [
                BindParamType(int, is_optional=True),
                BindParamType(str, is_optional=True),
            ],
        ),
        (
            "select * from (values (1,'kek')) as v (a,b) where a = any($1::integer[]) and b = any($2::varchar[]);",
            [
                BindParamType(list[int], is_optional=True),
                BindParamType(list[str], is_optional=True),
            ],
        ),
    ],
)
async def test_get_bind_params_types_for_query(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    expected_params: list[BindParamType],
) -> None:
    python_type_by_postgres_type = {
        "int4": int,
        "int4[]": list[int],
        "varchar": str,
        "varchar[]": list[str],
        "text": str,
    }

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(query)
        assert expected_params == await get_bind_params_python_types(
            prepared_statement=prepared_statement,
            python_type_by_postgres_type=python_type_by_postgres_type,
        )
