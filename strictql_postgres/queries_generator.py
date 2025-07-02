import asyncio
import dataclasses
from contextlib import asynccontextmanager
from typing import AsyncIterator

from pydantic import SecretStr

import asyncpg
from strictql_postgres.python_types import FilesContentByPath
from strictql_postgres.queries_to_generate import StrictQLQueriesToGenerate
from strictql_postgres.query_generator import (
    QueryToGenerate,
    generate_query_python_code,
)


@dataclasses.dataclass
class StrictqlGeneratorError(Exception):
    error: str


@asynccontextmanager
async def _create_pools(
    connection_strings_by_db_name: dict[str, SecretStr],
) -> AsyncIterator[dict[str, asyncpg.Pool]]:
    pools = {}
    for db_name, connection_url_secret in connection_strings_by_db_name.items():
        try:
            pools[db_name] = await asyncpg.create_pool(
                connection_url_secret.get_secret_value()
            ).__aenter__()
        except Exception as postgres_error:
            raise StrictqlGeneratorError(
                f"Cannot generate query code because error occurred during connection to database: {db_name}"
            ) from postgres_error

    try:
        yield pools
    finally:
        for db_name, pool in pools.items():
            await pool.__aexit__(None, None, None)


async def generate_queries(
    queries_to_generate: StrictQLQueriesToGenerate,
) -> FilesContentByPath:
    dbs_connection_urls = {
        database_name: database.connection_url
        for database_name, database in queries_to_generate.databases.items()
    }
    async with _create_pools(dbs_connection_urls) as pools:
        tasks = []

        for (
            file_path,
            query_to_generate,
        ) in queries_to_generate.queries_to_generate.items():
            task = asyncio.create_task(
                generate_query_python_code(
                    query_to_generate=QueryToGenerate(
                        query=query_to_generate.query,
                        function_name=query_to_generate.function_name,
                        params=query_to_generate.parameters,
                        query_type=query_to_generate.query_type,
                    ),
                    connection_pool=pools[query_to_generate.database_name],
                ),
                name=f"generate_code_for_query {query_to_generate.function_name} to {file_path}",
            )

            tasks.append(task)

        results = await asyncio.gather(*tasks)

        files = {}
        for code, file_path in zip(
            results, queries_to_generate.queries_to_generate.keys()
        ):
            files[file_path] = code

        return files
