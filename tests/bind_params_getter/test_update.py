import pytest

import asyncpg
from strictql_postgres.pg_bind_params_type_getter import (
    BindParamType,
    get_bind_params_python_types,
)


@pytest.mark.parametrize(
    ["create_table_query", "update_query", "expected_bind_params"],
    [
        (
            "create table kek (id integer not null, name varchar)",
            "update kek set id = $1, name = $2",
            [
                BindParamType(type_=int, is_optional=True),
                BindParamType(type_=str, is_optional=True),
            ],
        ),
    ],
)
async def test_update_query(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    create_table_query: str,
    update_query: str,
    expected_bind_params: list[BindParamType],
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute(create_table_query)

        prepared_statement = await connection.prepare(update_query)
        assert (
            await get_bind_params_python_types(
                prepared_statement=prepared_statement,
                python_type_by_postgres_type={
                    "int4": int,
                    "varchar": str,
                    "text": str,
                },
            )
            == expected_bind_params
        )
