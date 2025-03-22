import asyncpg
import pytest

from strictql_postgres.pg_bind_params_type_getter import (
    BindParamType,
    get_bind_params_python_types,
)


@pytest.mark.parametrize(
    ["create_table_query", "delete_query", "expected_bind_params"],
    [
        (
            "create table kek (id integer not null, name varchar)",
            "delete from kek where id = $1 or name = $2",
            [
                BindParamType(type_=int, is_optional=True),
                BindParamType(type_=str, is_optional=True),
            ],
        ),
    ],
)
async def test_delete_query(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    create_table_query: str,
    delete_query: str,
    expected_bind_params: list[BindParamType],
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute(create_table_query)

        prepared_statement = await connection.prepare(delete_query)
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
