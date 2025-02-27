import asyncpg
import pglast
import pytest

from strictql_postgres.pg_bind_params_type_getter import (
    PgBindParamTypeNotSupportedError,
    get_bind_params_python_types,
)


async def test_get_bind_params_types_for_query_with_params_when_not_supported_type(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        sql = "select $1"
        prepared_statement = await connection.prepare(sql)
        with pytest.raises(PgBindParamTypeNotSupportedError) as error:
            await get_bind_params_python_types(
                prepared_statement=prepared_statement,
                python_type_by_postgres_type={},
                parsed_sql=pglast.parse_sql(sql),
                make_bind_params_more_optional=False,
                connection=connection,
            )
        assert error.value.postgres_type == "text"


@pytest.mark.xfail()
async def test_get_bind_params_types_for_query_with_params_when_multiple_statements(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.fetch("select $1; select $2", 1, 2)
        sql = "select $1; select $2"
        await connection.prepare(sql)
        # with pytest.raises(MultipleStatementsNotSupportedYet) as error:
        #     await get_bind_params_python_types(
        #         prepared_statement=prepared_statement,
        #         python_type_by_postgres_type={},
        #         parsed_sql=pglast.parse_sql(sql),
        #         make_bind_params_more_optional=False,
        #         connection=connection,
        #     )
