import asyncio
import dataclasses
import shutil
from contextlib import asynccontextmanager
from typing import AsyncIterator

from pydantic import SecretStr

import asyncpg
from strictql_postgres.meta_file import generate_meta_file
from strictql_postgres.queries_to_generate import StrictQLQueriesToGenerate
from strictql_postgres.query_generator import (
    QueryToGenerate,
    generate_query_python_code,
)

STRICTQL_META_FILE_NAME = "strictql_meta"


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


async def generate_queries(queries_to_generate: StrictQLQueriesToGenerate) -> None:
    if queries_to_generate.generated_code_path.exists():
        meta_file_content_path = (
            queries_to_generate.generated_code_path / STRICTQL_META_FILE_NAME
        )
        if not meta_file_content_path.exists():
            raise StrictqlGeneratorError(
                error=f"Generated code directory: `{queries_to_generate.generated_code_path.resolve()}` already exists and does not contain a meta file {STRICTQL_META_FILE_NAME}."
                f" You probably specified the wrong directory or deleted the meta file. If you deleted the meta file yourself, then you need to manually delete the directory and regenerate the code."
            )
        meta_file_content = meta_file_content_path.read_text()
        expected_meta_file = generate_meta_file(
            path=queries_to_generate.generated_code_path,
            meta_file_name=STRICTQL_META_FILE_NAME,
        )
        if expected_meta_file != meta_file_content:
            raise StrictqlGeneratorError(
                error=f"Generated code directory: `{queries_to_generate.generated_code_path.resolve()}` already exists and generated files in it are not equals to meta file content {STRICTQL_META_FILE_NAME}, looks like generated has been changed manually."
                f" Delete the generated code directory and regenerate the code."
            )

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

        queries_to_generate.generated_code_path.mkdir(exist_ok=True)
        temp_dir_path = (
            queries_to_generate.generated_code_path.parent / "generated_code_path_new"
        )
        temp_dir_path.mkdir()

        for code, file_path in zip(
            results, queries_to_generate.queries_to_generate.keys()
        ):
            relative_path = file_path.resolve().relative_to(
                queries_to_generate.generated_code_path.resolve()
            )
            path = temp_dir_path / relative_path
            if path.parent != queries_to_generate.generated_code_path:
                path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(data=code)

        new_meta_file_content = generate_meta_file(
            path=temp_dir_path, meta_file_name=STRICTQL_META_FILE_NAME
        )

        (temp_dir_path / STRICTQL_META_FILE_NAME).write_text(new_meta_file_content)
        old_path = (
            queries_to_generate.generated_code_path.parent / "generated_code_path_old"
        )
        shutil.move(
            queries_to_generate.generated_code_path,
            old_path,
        )
        temp_dir_path.rename(queries_to_generate.generated_code_path)
        shutil.rmtree(old_path)
