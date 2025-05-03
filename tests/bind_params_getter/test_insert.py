import pytest

import asyncpg
from strictql_postgres.pg_bind_params_type_getter import (
    BindParamType,
    get_bind_params_python_types,
)


@pytest.mark.parametrize(
    ["create_table_query", "insert_query", "expected_bind_params"],
    [
        (
            "create table kek (id integer not null, name varchar)",
            "insert into kek (id, name) values ($1, $2)",
            [
                BindParamType(type_=int, is_optional=True),
                BindParamType(type_=str, is_optional=True),
            ],
        ),
        (
            "create table kek (id integer not null, name varchar)",
            "insert into kek (id, name) select * from unnest($1::integer[], $2::varchar[])",
            [
                BindParamType(type_=list[int], is_optional=True),
                BindParamType(type_=list[str], is_optional=True),
            ],
        ),
    ],
)
async def test_insert_query(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    create_table_query: str,
    insert_query: str,
    expected_bind_params: list[BindParamType],
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute(create_table_query)

        prepared_statement = await connection.prepare(insert_query)
        assert (
            await get_bind_params_python_types(
                prepared_statement=prepared_statement,
                python_type_by_postgres_type={
                    "int4": int,
                    "int4[]": list[int],
                    "varchar": str,
                    "varchar[]": list[str],
                    "text": str,
                },
            )
            == expected_bind_params
        )
