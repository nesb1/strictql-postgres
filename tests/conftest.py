import pathlib
from typing import AsyncIterator

import pytest

import asyncpg
from strictql_postgres.code_quality import CodeFixer

POSTGRES_HOST = "127.0.0.1"
POSTGRES_PORT = 5432
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "password"
POSTGRES_TEST_DB = "test_db"


@pytest.fixture()
async def asyncpg_connection_to_test_db() -> AsyncIterator[asyncpg.Connection]:
    connect_to_postgres_database: asyncpg.Connection = await asyncpg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database="postgres",
    )
    await connect_to_postgres_database.execute(
        f"drop database if exists {POSTGRES_TEST_DB}",
    )

    await connect_to_postgres_database.execute(
        f"create database {POSTGRES_TEST_DB}",
    )

    connect_to_test_database: asyncpg.Connection = await asyncpg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_TEST_DB,
    )

    try:
        yield connect_to_test_database
    finally:
        await connect_to_test_database.close()

        await connect_to_postgres_database.execute(
            f"drop database {POSTGRES_TEST_DB}",
        )
        await connect_to_postgres_database.close()


@pytest.fixture()
async def asyncpg_connection_pool_to_test_db() -> AsyncIterator[asyncpg.Pool]:
    connect_to_postgres_database: asyncpg.Connection = await asyncpg.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database="postgres",
    )
    await connect_to_postgres_database.execute(
        f"drop database if exists {POSTGRES_TEST_DB}",
    )

    await connect_to_postgres_database.execute(
        f"create database {POSTGRES_TEST_DB}",
    )

    try:
        async with asyncpg.create_pool(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_TEST_DB,
        ) as connection_pool_to_test_database:
            yield connection_pool_to_test_database
    finally:
        await connect_to_postgres_database.execute(
            f"drop database {POSTGRES_TEST_DB}",
        )
        await connect_to_postgres_database.close()


# stubs for packages without typing support located in a project root
PROJECT_ROOT = pathlib.Path(__file__).parent.parent


@pytest.fixture()
def code_quality_improver() -> CodeFixer:
    return CodeFixer()
