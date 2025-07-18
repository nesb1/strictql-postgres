import asyncio
import dataclasses
import pathlib
from contextlib import asynccontextmanager
from typing import AsyncIterator

from pydantic import SecretStr

import asyncpg
from strictql_postgres.format_exception import format_exception
from strictql_postgres.python_types import FilesContentByPath
from strictql_postgres.queries_to_generate import (
    QueryToGenerate,
    StrictQLQueriesToGenerate,
)
from strictql_postgres.query_generator import (
    QueryPythonCodeGeneratorError,
    QueryToGenerateInfo,
    generate_query_python_code,
)


@dataclasses.dataclass(frozen=True)
class QueryGeneratorError:
    query_to_generate: QueryToGenerate
    query_to_generate_path: pathlib.Path
    error: str


@dataclasses.dataclass
class QueriesGeneratorErrors(Exception):
    errors: list[QueryGeneratorError]


@dataclasses.dataclass
class PostgresConnectionError(Exception):
    error: str
    database: str


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
            raise PostgresConnectionError(
                error=format_exception(postgres_error),
                database=db_name,
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
                    query_to_generate=QueryToGenerateInfo(
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

        results = await asyncio.gather(*tasks, return_exceptions=True)
        errors = []
        success = []
        for (file_path, query_to_generate), result in zip(
            queries_to_generate.queries_to_generate.items(), results
        ):
            if isinstance(result, QueryPythonCodeGeneratorError):
                errors.append(
                    QueryGeneratorError(
                        query_to_generate=query_to_generate,
                        query_to_generate_path=file_path.resolve(),
                        error=result.error,
                    )
                )
                continue
            if isinstance(result, BaseException):
                raise result
            success.append(result)

        if len(errors) > 0:
            raise QueriesGeneratorErrors(
                errors=errors,
            )

        files = {}
        for code, file_path in zip(
            success, queries_to_generate.queries_to_generate.keys()
        ):
            files[file_path] = code

        return files
