import dataclasses
import enum
import types
from typing import assert_never

import pydantic
import pytest

import asyncpg
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.query_generator import (
    QueryToGenerateInfo,
    generate_query_python_code,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.supported_postgres_types import (
    ALL_SUPPORTED_POSTGRES_TYPES,
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)
from tests.pg_types_test_data import (
    TEST_DATA_FOR_ALL_TYPES,
    TEST_DATA_FOR_SIMPLE_TYPES,
    TEST_DATA_FOR_TYPES_WITH_IMPORT,
)


@dataclasses.dataclass
class TypeTestData:
    query_literal: str
    expected_python_value: object


@pytest.mark.parametrize(
    ("postgres_value", "cast", "expected_python_value"),
    [
        (
            test_data.test_data.postgres_value_as_str,
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_value,
        )
        for data_type in SupportedPostgresSimpleTypes
        for test_data in TEST_DATA_FOR_SIMPLE_TYPES[data_type]
    ],
)
async def test_generate_code_and_execute_for_simple_types_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    postgres_value: str,
    cast: str,
    expected_python_value: object,
    code_quality_improver: CodeFixer,
) -> None:
    query = f"select ({postgres_value})::{cast} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            params={},
            query_type="fetch",
            function_name=StringInSnakeLowerCase(function_name),
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection)  # type: ignore[misc]
        if isinstance(res[0].value, float):  # type: ignore[misc]
            assert res[0].value == pytest.approx(expected_python_value)  # type: ignore[misc]
        else:
            assert res[0].value == expected_python_value  # type: ignore[misc]

    model: pydantic.BaseModel = generated_module.FetchAllTestModel
    assert (
        model.model_fields["value"].annotation == type(expected_python_value) | None  # type: ignore[misc]
    )


@pytest.mark.parametrize(
    ("postgres_value", "cast", "expected_python_value"),
    [
        (
            test_data.test_data.postgres_value_as_str,
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
        for test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type]
    ],
)
async def test_generate_code_and_execute_for_types_with_import_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    postgres_value: str,
    cast: str,
    expected_python_value: object,
    code_quality_improver: CodeFixer,
) -> None:
    query = f"select ({postgres_value})::{cast} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            function_name=StringInSnakeLowerCase(function_name),
            params={},
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection)  # type: ignore[misc]

        assert res[0].value == expected_python_value  # type: ignore[misc]

    model: pydantic.BaseModel = generated_module.FetchAllTestModel
    assert (
        model.model_fields["value"].annotation == type(expected_python_value) | None  # type: ignore[misc]
    )


class ArrayTestCases(enum.Enum):
    None_ = "none"
    ArrayOfNone = "array_of_none"
    ArrayOfArraysOfNone = "array_of_arrays_of_none"
    Array = "array"
    ArrayOfArrays = "array_of_arrays"
    ArrayOfArraysOfArrays = "array_of_arrays_of_arrays"


@pytest.mark.parametrize("test_case", [test_case for test_case in ArrayTestCases])
@pytest.mark.parametrize(
    ("data_type_literal", "python_value", "postgres_data_type", "expected_python_type"),
    [
        (
            test_data.test_data.postgres_value_as_str,
            test_data.test_data.expected_python_value,
            test_data.test_data.cast_str,
            test_data.test_data.expected_python_type,
        )
        for postgres_data_type in ALL_SUPPORTED_POSTGRES_TYPES
        for test_data in TEST_DATA_FOR_ALL_TYPES[postgres_data_type]
    ],
)
async def test_generate_code_and_execute_for_array_types_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    data_type_literal: str,
    python_value: object,
    postgres_data_type: str,
    test_case: ArrayTestCases,
    code_quality_improver: CodeFixer,
    expected_python_type: type[object],
) -> None:
    query_literal: str
    expected_python_value: object
    if issubclass(expected_python_type, float):
        python_value = pytest.approx(python_value)
    match test_case:
        case ArrayTestCases.None_:
            query_literal = f"(null)::{postgres_data_type}[]"
            expected_python_value = None
        case ArrayTestCases.ArrayOfNone:
            query_literal = f"(ARRAY[null])::{postgres_data_type}[]"
            expected_python_value = [None]
        case ArrayTestCases.ArrayOfArraysOfNone:
            query_literal = f"(ARRAY[ARRAY[null],ARRAY[null]])::{postgres_data_type}[]"
            expected_python_value = [[None], [None]]
        case ArrayTestCases.Array:
            query_literal = f"(ARRAY[{data_type_literal}])::{postgres_data_type}[]"
            expected_python_value = [python_value]
        case ArrayTestCases.ArrayOfArrays:
            query_literal = f"(ARRAY[ARRAY[{data_type_literal}],ARRAY[{data_type_literal}]])::{postgres_data_type}[]"
            expected_python_value = [[python_value], [python_value]]
        case ArrayTestCases.ArrayOfArraysOfArrays:
            query_literal = f"(ARRAY[ARRAY[ARRAY[{data_type_literal}]],ARRAY[array[{data_type_literal}]]])::{postgres_data_type}[]"
            expected_python_value = [[[python_value]], [[python_value]]]
        case _:
            assert_never(test_case)

    query = f"select {query_literal} as value"
    function_name = "fetch_all_test"

    code = await generate_query_python_code(
        query_to_generate=QueryToGenerateInfo(
            query=query,
            function_name=StringInSnakeLowerCase(function_name),
            params={},
            query_type="fetch",
        ),
        connection_pool=asyncpg_connection_pool_to_test_db,
    )

    generated_module = types.ModuleType("generated_module")

    exec(code, generated_module.__dict__)  # type: ignore[misc]

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        res = await generated_module.fetch_all_test(connection)  # type: ignore[misc]
        assert res[0].value == expected_python_value  # type: ignore[misc]
