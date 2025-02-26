import asyncpg
import pytest

from strictql_postgres.common_types import ColumnType
from strictql_postgres.pg_response_schema_getter import (
    get_pg_response_schema_from_prepared_statement,
    PgResponseSchema,
    PgResponseSchemaTypeNotSupportedError,
)


@pytest.mark.parametrize(
    ("query", "expected_schema"),
    [
        (
            "select (1::int4) as id, ('kek'::varchar) as name",
            {
                "id": ColumnType(type_=int, is_optional=True),
                "name": ColumnType(type_=str, is_optional=True),
            },
        )
    ],
)
async def test_get_pg_response_schema_from_prepared_statement(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    expected_schema: PgResponseSchema,
) -> None:
    python_type_by_postgres_type = {
        "int4": int,
        "varchar": str,
        "text": str,
    }

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(query=query)
        assert (
            get_pg_response_schema_from_prepared_statement(
                prepared_stmt=prepared_stmt,
                python_type_by_postgres_type=python_type_by_postgres_type,
            )
            == expected_schema
        )


async def test_get_pg_response_schema_from_prepared_statement_raises_error_when_not_supported_type(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_stmt = await connection.prepare(query="select 1 as v")
        with pytest.raises(PgResponseSchemaTypeNotSupportedError) as error:
            get_pg_response_schema_from_prepared_statement(
                prepared_stmt=prepared_stmt,
                python_type_by_postgres_type={},
            )

        assert error.value.postgres_type == "int4"
        assert error.value.column_name == "v"
