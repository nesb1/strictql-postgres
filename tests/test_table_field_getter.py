import pytest

import asyncpg
from strictql_postgres.table_field_getter import (
    TableField,
    get_table_fields,
    TableNotExistsError,
)


@pytest.mark.parametrize(
    ("create_table", "table_name", "expected_fields"),
    [
        (
            "create table kek(id integer, name varchar)",
            "kek",
            {
                "id": TableField(num=1, not_null=False, type_id=23),
                "name": TableField(num=2, not_null=False, type_id=1043),
            },
        ),
        ("create table kek()", "kek", {}),
    ],
)
async def test_get_table_fields(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    create_table: str,
    expected_fields: dict[str, TableField],
    table_name: str,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute(create_table)

        assert (
            await get_table_fields(connection=connection, table_name=table_name)
            == expected_fields
        )


async def test_get_not_existing_table_fields(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        with pytest.raises(TableNotExistsError):
            await get_table_fields(
                connection=connection, table_name="not_existed_table"
            )
