import inspect
import types
from collections.abc import Sequence

import pytest

import asyncpg
from strictql_postgres.code_quality import CodeQualityImprover
from strictql_postgres.query_generator import (
    InvalidParamNames,
    InvalidSqlQuery,
    QueryToGenerate,
    generate_query_python_code,
)


@pytest.mark.parametrize("query", ["sselect 1", "invalid_query"])
async def test_query_invalid(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query: str,
    code_quality_improver: CodeQualityImprover,
) -> None:
    function_name = "fetch_all_test"

    with pytest.raises(InvalidSqlQuery) as error:
        await generate_query_python_code(
            query_to_generate=QueryToGenerate(
                query=query,
                function_name=function_name,
                param_names=[],
                return_type="list",
            ),
            connection_pool=asyncpg_connection_pool_to_test_db,
        )

    assert "syntax error at or near" in error.value.postgres_error
    assert error.value.query == query


async def test_param_names_equals_query_bind_params(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    code_quality_improver: CodeQualityImprover,
) -> None:
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerate(
            query="select $1::integer as v1, $2::integer as v2",
            function_name=function_name,
            param_names=["param1", "param2"],
            return_type="list",
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
    code_quality_improver: CodeQualityImprover,
) -> None:
    function_name = "fetch_all_test"

    with pytest.raises(InvalidParamNames) as error:
        await generate_query_python_code(
            query_to_generate=QueryToGenerate(
                query=query,
                function_name=function_name,
                param_names=param_names,
                return_type="list",
            ),
            connection_pool=asyncpg_connection_pool_to_test_db,
        )

    assert error.value.actual_param_names == param_names
    assert error.value.expected_param_names_count == expected_param_names
