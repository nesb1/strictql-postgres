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
        pytest.param(
            "create table kek (id integer not null, name varchar)",
            "insert into kek (id, name) values ($1, $2)",
            [
                BindParamType(type_=int, is_optional=False),
                BindParamType(type_=str, is_optional=True),
            ],
            id="simple case",
        ),
        pytest.param(
            "create table kek (id integer not null, name varchar)",
            "insert into kek (name, id) values ($1, $2)",
            [
                BindParamType(type_=str, is_optional=True),
                BindParamType(type_=int, is_optional=False),
            ],
            id="unordered params",
        ),
        pytest.param(
            "create table kek (id integer not null, name varchar)",
            "insert into kek (id) values ($1)",
            [
                BindParamType(type_=int, is_optional=False),
            ],
            id="only required params",
        ),
        pytest.param(
            "create table kek (id integer, name varchar)",
            "insert into kek (id, name) values (DEFAULT, DEFAULT)",
            [],
            id="with only default values per column",
        ),
        pytest.param(
            "create table kek (id integer, name varchar)",
            "insert into kek (id, name) DEFAULT VALUES ",
            [],
            id="with only default values for all columns",
        ),
        pytest.param(
            "create table kek (col1 integer not null, col2 varchar, col3 varchar not null)",
            "insert into kek (col2, col1, col3) values (DEFAULT, $1, $2)",
            [
                BindParamType(type_=str, is_optional=True),
                BindParamType(type_=str, is_optional=False),
            ],
            id="with not only default values",
        ),
        pytest.param(
            "create table kek (col1 integer not null, col2 varchar)",
            "insert into kek (col1, col2) values (repeat($1,1), repeat($2,1))",
            [
                BindParamType(
                    type_=str, is_optional=True
                ),  # on real query with null it will fail, but it is too hard to check just now
                BindParamType(type_=str, is_optional=True),
            ],
            id="only functions in insert value",
        ),
        pytest.param(
            "create table kek (col1 integer not null, col2 varchar, col3 varchar not null)",
            "insert into kek (col1, col2, col3) values (repeat($1,1), repeat($2,1), $3)",
            [
                BindParamType(type_=str, is_optional=True),
                BindParamType(type_=str, is_optional=True),
                BindParamType(type_=str, is_optional=False),
            ],
            id="functions in insert value combined with simple values",
        ),
        pytest.param(
            "create table kek (col1 varchar not null, col2 varchar not null)",
            "insert into kek (col1, col2) values (repeat(repeat(repeat($1,1),1),1), $2)",
            [
                BindParamType(type_=str, is_optional=True),
                BindParamType(type_=str, is_optional=True),
            ],
            id="inner functions in insert values",
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


async def test_insert_query_with_function(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute("create table kek (col varchar not null)")
        query = "insert into kek (col) values (repeat($1, 4))"
        prepared_statement = await connection.prepare(query)
        assert await get_bind_params_python_types(
            prepared_statement=prepared_statement,
            python_type_by_postgres_type={
                "int4": int,
                "varchar": str,
                "text": str,
            },
            parsed_sql=pglast.parse_sql(query),
            connection=connection,
            make_bind_params_more_optional=False,
        ) == [
            BindParamType(type_=str, is_optional=True),
        ]
