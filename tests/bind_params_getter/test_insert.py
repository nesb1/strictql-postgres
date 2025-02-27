import asyncpg
import pglast
import pytest

from strictql_postgres.pg_bind_params_type_getter import (
    BindParamType,
    get_bind_params_python_types,
)


@pytest.mark.parametrize("make_params_more_optional", (True, False))
@pytest.mark.parametrize(
    ["create_table_query", "insert_query", "expected_bind_params"],
    [
        (
            "create table kek (id integer not null, name varchar)",
            "insert into kek (id, name) values ($1, $2)",
            [
                BindParamType(type_=int, is_optional=False),
                BindParamType(type_=str, is_optional=True),
            ],
        ),
    ],
)
async def test_insert_query(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    create_table_query: str,
    insert_query: str,
    expected_bind_params: list[BindParamType],
    make_params_more_optional: bool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute(create_table_query)

        prepared_statement = await connection.prepare(insert_query)
        assert (
            await get_bind_params_python_types(
                prepared_statement=prepared_statement,
                python_type_by_postgres_type={
                    "int4": int,
                    "varchar": str,
                    "text": str,
                },
                parsed_sql=pglast.parse_sql(insert_query),
                make_bind_params_more_optional=make_params_more_optional,
                connection=connection,
            )
            == expected_bind_params
        )
