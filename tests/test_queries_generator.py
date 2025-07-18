import pathlib
from unittest import mock
from unittest.mock import AsyncMock

import pytest
from pydantic import SecretStr

from strictql_postgres.queries_generator import (
    PostgresConnectionError,
    QueriesGeneratorErrors,
    QueryGeneratorError,
    generate_queries,
)
from strictql_postgres.queries_to_generate import (
    DataBaseSettings,
    QueryToGenerate,
    StrictQLQueriesToGenerate,
)
from strictql_postgres.query_generator import QueryPythonCodeGeneratorError
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase


async def test_strictql_generator_works() -> None:
    db_connection_url = SecretStr("postgresql://postgres:password@localhost/postgres")

    await generate_queries(
        queries_to_generate=StrictQLQueriesToGenerate(
            queries_to_generate={
                pathlib.Path("file_1"): QueryToGenerate(
                    query="select 1 as value",
                    parameters={},
                    database_name="db",
                    database_connection_url=db_connection_url,
                    query_type="fetch",
                    function_name=StringInSnakeLowerCase("query"),
                ),
                pathlib.Path("file_2"): QueryToGenerate(
                    query="select 2 as value",
                    parameters={},
                    database_name="db",
                    database_connection_url=db_connection_url,
                    query_type="fetch",
                    function_name=StringInSnakeLowerCase("query"),
                ),
            },
            databases={"db": DataBaseSettings(connection_url=db_connection_url)},
            generated_code_path=pathlib.Path("generated_code"),
        )
    )


async def test_strictql_generator_handle_query_generator_error() -> None:
    with mock.patch(
        "strictql_postgres.queries_generator.generate_query_python_code",
        new=AsyncMock(),
    ) as mocked_generate_query_python_code:
        query_generator_error1 = "kek"
        query_generator_error2 = "eke"
        mocked_generate_query_python_code.side_effect = [  # type: ignore[misc]
            "a=1",
            QueryPythonCodeGeneratorError(query_generator_error1),
            QueryPythonCodeGeneratorError(query_generator_error2),
        ]
        db_connection_url = SecretStr(
            "postgresql://postgres:password@localhost/postgres"
        )

        query_to_generate = QueryToGenerate(
            query="select 1 as value",
            function_name=StringInSnakeLowerCase("select_1"),
            parameters={},
            database_name="db",
            database_connection_url=db_connection_url,
            query_type="fetch",
        )
        with pytest.raises(QueriesGeneratorErrors) as error:
            await generate_queries(
                queries_to_generate=StrictQLQueriesToGenerate(
                    queries_to_generate={
                        pathlib.Path("query1.py"): query_to_generate,
                        pathlib.Path("query2.py"): query_to_generate,
                        pathlib.Path("query3.py"): query_to_generate,
                    },
                    databases={
                        "db": DataBaseSettings(connection_url=db_connection_url)
                    },
                    generated_code_path=pathlib.Path(),
                )
            )
        assert error.value.errors == [
            QueryGeneratorError(
                query_to_generate=query_to_generate,
                error=query_generator_error1,
                query_to_generate_path=pathlib.Path("query2.py").resolve(),
            ),
            QueryGeneratorError(
                query_to_generate=query_to_generate,
                error=query_generator_error2,
                query_to_generate_path=pathlib.Path("query3.py").resolve(),
            ),
        ]


async def test_strictql_generator_handle_invalid_postgres_url() -> None:
    with pytest.raises(PostgresConnectionError) as error:
        await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={},
                databases={
                    "db": DataBaseSettings(
                        connection_url=SecretStr("invalid_postgres_url")
                    )
                },
                generated_code_path=pathlib.Path("query1.py"),
            )
        )
    assert (
        error.value.error
        == "<class 'asyncpg.exceptions._base.ClientConfigurationError'>: invalid DSN: scheme is expected to be either \"postgresql\" or \"postgres\", got ''"
    )


async def test_strictql_generator_handle_invalid_postgres_login_password() -> None:
    with pytest.raises(PostgresConnectionError) as error:
        await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={},
                databases={
                    "db": DataBaseSettings(
                        connection_url=SecretStr(
                            "postgresql://postgres:invalid_password@localhost/postgres"
                        )
                    )
                },
                generated_code_path=pathlib.Path("query1.py"),
            )
        )
    assert (
        error.value.error
        == "<class 'asyncpg.exceptions.InvalidPasswordError'>: password authentication failed for user \"postgres\""
    )
