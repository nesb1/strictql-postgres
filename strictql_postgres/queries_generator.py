import asyncio
import shutil
from contextlib import asynccontextmanager
from typing import AsyncIterator

from pydantic import SecretStr

import asyncpg
from strictql_postgres.config_manager import StrictqlSettings
from strictql_postgres.query_generator import (
    QueryToGenerate,
    generate_query_python_code,
)


class StrictqlGeneratorError(Exception):
    pass


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


async def generate_queries(settings: StrictqlSettings) -> None:
    dbs_connection_urls = {
        database_name: database.connection_url
        for database_name, database in settings.databases.items()
    }
    async with _create_pools(dbs_connection_urls) as pools:
        tasks = []

        for file_path, queries_to_generate in settings.queries_to_generate.items():
            for query_name, query_to_generate in queries_to_generate.items():
                task = asyncio.create_task(
                    generate_query_python_code(
                        query_to_generate=QueryToGenerate(
                            query=query_to_generate.query,
                            function_name=query_name,
                            params=query_to_generate.parameters,
                            return_type=query_to_generate.return_type,
                        ),
                        connection_pool=pools[query_to_generate.database_name],
                    ),
                    name=f"generate_code_for_query {query_name} to {file_path}",
                )

                tasks.append(task)

        results = await asyncio.gather(*tasks)
        if settings.generated_code_path.exists():
            shutil.rmtree(settings.generated_code_path)
        settings.generated_code_path.mkdir(exist_ok=False)

        for code, file_path in zip(results, settings.queries_to_generate.keys()):
            path = file_path
            if path.parent != settings.generated_code_path:
                path.parent.mkdir(parents=True)
            path.write_text(data=code)
