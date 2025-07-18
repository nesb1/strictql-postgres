import datetime
import inspect
import types
from collections.abc import Sequence
from unittest.mock import MagicMock, patch

import pytest

import asyncpg
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.pg_response_schema_getter import (
    PgResponseSchemaGetterError,
    PgResponseSchemaTypeNotSupported,
)
from strictql_postgres.queries_to_generate import Parameter
from strictql_postgres.query_generator import (
    QueryPythonCodeGeneratorError,
    QueryToGenerateInfo,
    generate_query_python_code,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase


@pytest.mark.parametrize("query", ["sselect 1", "invalid_query"])
async def test_query_invalid(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    code_quality_improver: CodeFixer,
) -> None:
    function_name = "fetch_all_test"

    with pytest.raises(QueryPythonCodeGeneratorError) as error:
        await generate_query_python_code(
            query_to_generate=QueryToGenerateInfo(
                query=query,
                function_name=StringInSnakeLowerCase(function_name),
                params={},
                query_type="fetch",
            ),
            connection_pool=asyncpg_connection_pool_to_test_db,
        )
    assert "syntax error at or near" in error.value.error


async def test_param_names_equals_query_bind_params(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    code_quality_improver: CodeFixer,
) -> None:
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query="select $1::integer as v1, $2::integer as v2",
            function_name=StringInSnakeLowerCase(function_name),
            params={
                "param1": Parameter(is_optional=True),
                "param2": Parameter(is_optional=True),
            },
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection, param1=1, param2=2)  # type: ignore[misc]

        assert res[0].v1 == 1  # type: ignore[misc]
        assert res[0].v2 == 2  # type: ignore[misc]

    assert inspect.get_annotations(generated_module.fetch_all_test) == {  # type: ignore[misc]
        "connection": asyncpg.connection.Connection,
        "param1": int | None,
        "param2": int | None,
        "timeout": datetime.timedelta | None,
        "return": Sequence[generated_module.FetchAllTestModel],  # type: ignore [name-defined]
    }


@pytest.mark.parametrize(
    ("query", "param_names", "expected_param_names"),
    [
        pytest.param("select $1::integer as v1, $2::integer as v2", [], 2),
        pytest.param("select $1::integer  as v1, $2::integer as v2", ["param1"], 2),
        pytest.param("select $1::integer  as v1, $2::integer as v2", ["param1"], 2),
    ],
)
async def test_param_names_not_equals_query_bind_params(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    param_names: list[str],
    expected_param_names: int,
    code_quality_improver: CodeFixer,
) -> None:
    function_name = "fetch_all_test"

    with pytest.raises(QueryPythonCodeGeneratorError) as error:
        params = {parm_name: Parameter(is_optional=True) for parm_name in param_names}
        await generate_query_python_code(
            query_to_generate=QueryToGenerateInfo(
                query=query,
                function_name=StringInSnakeLowerCase(function_name),
                params=params,
                query_type="fetch",
            ),
            connection_pool=asyncpg_connection_pool_to_test_db,
        )

    assert (
        error.value.error
        == f"Query contains invalid param names count, expected param names count: `{expected_param_names}`, actual_params_count: `{len(params)}`"
    )


async def test_handle_response_schema_getter_error(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    function_name = "fetch_all_test"

    with pytest.raises(QueryPythonCodeGeneratorError) as error:
        schema_error = PgResponseSchemaTypeNotSupported(
            postgres_type="kek", column_name="test"
        )
        with patch(
            "strictql_postgres.query_generator.get_pg_response_schema_from_prepared_statement",
            new=MagicMock(side_effect=PgResponseSchemaGetterError(error=schema_error)),
        ) as mock:
            await generate_query_python_code(
                query_to_generate=QueryToGenerateInfo(
                    query="select 1",
                    function_name=StringInSnakeLowerCase(function_name),
                    params={},
                    query_type="fetch",
                ),
                connection_pool=asyncpg_connection_pool_to_test_db,
            )

        assert mock.called
    assert (
        error.value.error == "Postgres type: `kek` in column: `test` not supported yet"
    )


async def test_generate_code_with_params_when_some_params_not_optional(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    code_quality_improver: CodeFixer,
) -> None:
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query="select $1::integer as v1, $2::integer as v2",
            function_name=StringInSnakeLowerCase(function_name),
            params={
                "param1": Parameter(is_optional=True),
                "param2": Parameter(is_optional=False),
            },
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection, param1=None, param2=2)  # type: ignore[misc]

        assert res[0].v1 is None  # type: ignore[misc]
        assert res[0].v2 == 2  # type: ignore[misc]

    assert inspect.get_annotations(generated_module.fetch_all_test) == {  # type: ignore[misc]
        "connection": asyncpg.connection.Connection,
        "param1": int | None,
        "param2": int,
        "timeout": datetime.timedelta | None,
        "return": Sequence[generated_module.FetchAllTestModel],  # type: ignore [name-defined]
    }
