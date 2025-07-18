import enum
from typing import assert_never

import pytest
from pydantic import BaseModel

import asyncpg
from asyncpg import Pool
from strictql_postgres.asyncpg_result_converter import (
    RangeType,
    convert_record_to_pydantic_model,
)
from strictql_postgres.supported_postgres_types import (
    ALL_SUPPORTED_POSTGRES_TYPES,
)
from tests.pg_types_test_data import TEST_DATA_FOR_ALL_TYPES, TypeTestData


@pytest.mark.parametrize(
    ("test_case"),
    [
        (test_case.test_data)
        for supported_type in ALL_SUPPORTED_POSTGRES_TYPES
        for test_case in TEST_DATA_FOR_ALL_TYPES[supported_type]
    ],
)
async def test_all_supported_types_converts(
    asyncpg_connection_pool_to_test_db: Pool, test_case: TypeTestData
) -> None:
    class Model(BaseModel):  # type:ignore[explicit-any]
        a: test_case.expected_python_type  # type:ignore[name-defined] # mypy wtf

    async with asyncpg_connection_pool_to_test_db.acquire() as pool:
        record = await pool.fetchrow(
            query=f"select ({test_case.postgres_value_as_str})::{test_case.cast_str} as a"
        )

        assert record is not None

        actual_model = convert_record_to_pydantic_model(
            record=record, pydantic_model_type=Model
        )
        if isinstance(test_case.expected_python_value, float):
            assert actual_model.a == pytest.approx(test_case.expected_python_value)  # type: ignore[misc]
        else:
            assert actual_model.a == test_case.expected_python_value  # type: ignore[misc]


class ArrayTestCases(enum.Enum):
    None_ = "none"
    ArrayOfNone = "array_of_none"
    ArrayOfArraysOfNone = "array_of_arrays_of_none"
    Array = "array"
    ArrayOfArrays = "array_of_arrays"
    ArrayOfArraysOfArrays = "array_of_arrays_of_arrays"


@pytest.mark.parametrize("test_case", [(test_case) for test_case in ArrayTestCases])
@pytest.mark.parametrize(
    ("test_data"),
    [
        (test_data.test_data)
        for supported_type in ALL_SUPPORTED_POSTGRES_TYPES
        for test_data in TEST_DATA_FOR_ALL_TYPES[supported_type]
    ],
)
async def test_array_converts(
    asyncpg_connection_pool_to_test_db: Pool,
    test_data: TypeTestData,
    test_case: ArrayTestCases,
) -> None:
    expected_python_value_array: object
    test_data_expected_python_value = (
        pytest.approx(test_data.expected_python_value)
        if isinstance(test_data.expected_python_value, float)
        else test_data.expected_python_value
    )
    match test_case:
        case ArrayTestCases.None_:
            query_literal = f"(null)::{test_data.cast_str}[]"
            expected_python_value_array = None
        case ArrayTestCases.ArrayOfNone:
            query_literal = f"(ARRAY[null])::{test_data.cast_str}[]"
            expected_python_value_array = [None]
        case ArrayTestCases.ArrayOfArraysOfNone:
            query_literal = f"(ARRAY[ARRAY[null],ARRAY[null]])::{test_data.cast_str}[]"
            expected_python_value_array = [[None], [None]]
        case ArrayTestCases.Array:
            query_literal = (
                f"(ARRAY[{test_data.postgres_value_as_str}])::{test_data.cast_str}[]"
            )
            expected_python_value_array = [test_data_expected_python_value]
        case ArrayTestCases.ArrayOfArrays:
            query_literal = f"(ARRAY[ARRAY[{test_data.postgres_value_as_str}],ARRAY[{test_data.postgres_value_as_str}]])::{test_data.cast_str}[]"
            expected_python_value_array = [
                [test_data_expected_python_value],
                [test_data_expected_python_value],
            ]
        case ArrayTestCases.ArrayOfArraysOfArrays:
            query_literal = f"(ARRAY[ARRAY[ARRAY[{test_data.postgres_value_as_str}]],ARRAY[array[{test_data.postgres_value_as_str}]]])::{test_data.cast_str}[]"
            expected_python_value_array = [
                [[test_data_expected_python_value]],
                [[test_data_expected_python_value]],
            ]
        case _:
            assert_never(test_case)

    class Model(BaseModel):  # type:ignore[explicit-any]
        a: (  # type: ignore[name-defined]
            list[
                test_data.expected_python_type
                | None
                | list[
                    test_data.expected_python_type
                    | None
                    | list[test_data.expected_python_type | None | object]
                ]
            ]
            | None
        )

    async with asyncpg_connection_pool_to_test_db.acquire() as pool:
        record = await pool.fetchrow(query=f"select {query_literal} as a")

        assert record is not None

        actual_model = convert_record_to_pydantic_model(
            record=record, pydantic_model_type=Model
        )

        assert actual_model.a == expected_python_value_array


async def test_convert_record_with_range_type(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        record = await connection.fetchrow(query="select int4range(10,20) as value")

        class Model(BaseModel):  # type: ignore[explicit-any]
            value: RangeType

        assert record is not None

        res = convert_record_to_pydantic_model(record=record, pydantic_model_type=Model)
        assert res == Model(value=RangeType(a=10, b=20))
