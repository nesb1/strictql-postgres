import datetime
import inspect
import types
from collections.abc import Sequence

import pydantic
import pytest

import asyncpg
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.queries_to_generate import Parameter
from strictql_postgres.query_generator import (
    QueryToGenerateInfo,
    generate_query_python_code,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.supported_postgres_types import (
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)
from tests.pg_types_test_data import (
    TEST_DATA_FOR_SIMPLE_TYPES,
    TEST_DATA_FOR_TYPES_WITH_IMPORT,
)


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_value,
        )
        for simple_type in SupportedPostgresSimpleTypes
        for test_data in TEST_DATA_FOR_SIMPLE_TYPES[simple_type]
    ],
)
async def test_generate_code_and_execute_for_simple_types_in_bind_param(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    code_quality_improver: CodeFixer,
    bind_param_cast: str,
    param: object,
) -> None:
    query = f"select $1::{bind_param_cast} as value"

    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            params={"param": Parameter(is_optional=True)},
            query_type="fetch",
            function_name=StringInSnakeLowerCase(function_name),
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection, param=param)  # type: ignore[misc]
        if isinstance(param, float):
            assert res[0].value == pytest.approx(param)  # type: ignore[misc]
        else:
            assert res[0].value == param  # type: ignore[misc]

    assert inspect.get_annotations(generated_module.fetch_all_test) == {  # type: ignore[misc]
        "connection": asyncpg.connection.Connection,
        "param": type(param) | None,
        "timeout": datetime.timedelta | None,
        "return": Sequence[generated_module.FetchAllTestModel],  # type: ignore [name-defined]
    }

    model: pydantic.BaseModel = generated_module.FetchAllTestModel
    assert (
        model.model_fields["value"].annotation == type(param) | None  # type: ignore[misc]
    )


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
        for test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type]
    ],
)
async def test_generate_code_and_execute_for_types_with_import_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    bind_param_cast: str,
    param: object,
    code_quality_improver: CodeFixer,
) -> None:
    query = f"select $1::{bind_param_cast} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            function_name=StringInSnakeLowerCase(function_name),
            params={"param": Parameter(is_optional=True)},
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection, param=param)  # type: ignore[misc]
        if isinstance(param, float):
            assert res[0].value == pytest.approx(param)  # type: ignore[misc]
        else:
            assert res[0].value == param  # type: ignore[misc]

    assert inspect.get_annotations(generated_module.fetch_all_test) == {  # type: ignore[misc]
        "connection": asyncpg.connection.Connection,
        "param": type(param) | None,
        "timeout": datetime.timedelta | None,
        "return": Sequence[generated_module.FetchAllTestModel],  # type: ignore [name-defined]
    }


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
        for test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type]
    ],
)
async def test_generate_code_and_execute_for_types_with_import_in_response_model_when_no_response_models(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    bind_param_cast: str,
    param: object,
    code_quality_improver: CodeFixer,
) -> None:
    query = f"select $1::{bind_param_cast} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            function_name=StringInSnakeLowerCase(function_name),
            params={"param": Parameter(is_optional=True)},
            query_type="execute",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection, param=param)  # type: ignore[misc]
        assert res == "SELECT 1"  # type: ignore[misc]

    assert inspect.get_annotations(generated_module.fetch_all_test) == {  # type: ignore[misc]
        "connection": asyncpg.connection.Connection,
        "param": type(param) | None,
        "timeout": datetime.timedelta | None,
        "return": str,
    }


@pytest.mark.parametrize("dimension", [1, 2, 3, 6])
@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
        for test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type]
    ],
)
async def test_generate_code_and_execute_for_array_types(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    bind_param_cast: str,
    param: object,
    code_quality_improver: CodeFixer,
    dimension: int,
) -> None:
    if isinstance(param, float):
        param = pytest.approx(param)

    array_cast_str = "".join(["[]" for _ in range(dimension)])

    param_as_array: list[object] = []
    last_inner_array: list[object] = param_as_array
    for _ in range(dimension - 1):
        new_inner_array: list[object] = []
        last_inner_array.append(new_inner_array)
        last_inner_array = new_inner_array

    last_inner_array.append(param)

    query = f"select $1::{bind_param_cast}{array_cast_str} as value"

    function_name = "test_func"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            function_name=StringInSnakeLowerCase(function_name),
            params={"param": Parameter(is_optional=True)},
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.test_func(connection, param=param_as_array)  # type: ignore[misc]
        assert res[0].value == param_as_array  # type: ignore[misc]
    expected_param_type = (
        list[  # type: ignore[misc, valid-type]
            type(param)
            | None
            | list[type(param) | None | list[type(param) | None | object]]  # type: ignore[misc]
        ]
        | None
    )
    assert inspect.get_annotations(generated_module.test_func) == {  # type: ignore[misc]
        "connection": asyncpg.connection.Connection,
        "param": expected_param_type,
        "timeout": datetime.timedelta | None,
        "return": Sequence[generated_module.TestFuncModel],  # type: ignore [name-defined]
    }
