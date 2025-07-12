import dataclasses
import enum
import typing
from typing import assert_never

import pytest
from pydantic import BaseModel
from typing_extensions import TypeAliasType

import asyncpg
from asyncpg import Pool
from strictql_postgres.asyncpg_result_converter import (
    RangeType,
    convert_record_to_pydantic_model,
)
from strictql_postgres.supported_postgres_types import (
    ALL_SUPPORTED_POSTGRES_TYPES,
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)


@dataclasses.dataclass
class TypeConverterTestData:
    python_type: type[object]
    postgres_type: str
    postgres_value: str
    python_value: object


SUPPORTED_TYPES_TEST_DATA: dict[
    SupportedPostgresSimpleTypes | SupportedPostgresTypeRequiredImports,
    list[TypeConverterTestData],
] = {
    SupportedPostgresSimpleTypes.BOOL: [
        TypeConverterTestData(
            python_type=int,
            postgres_type="bool",
            postgres_value="true",
            python_value=True,
        )
    ],
    SupportedPostgresSimpleTypes.INTEGER: [
        TypeConverterTestData(
            python_type=int,
            postgres_type="integer",
            postgres_value="1",
            python_value=1,
        ),
        TypeConverterTestData(
            python_type=int,
            postgres_type="integer",
            postgres_value="0",
            python_value=0,
        ),
        TypeConverterTestData(
            python_type=int,
            postgres_type="integer",
            postgres_value="-1",
            python_value=-1,
        ),
    ],
    SupportedPostgresSimpleTypes.TEXT: [
        TypeConverterTestData(
            python_type=str,
            postgres_type="varchar",
            postgres_value="'value'",
            python_value="value",
        ),
        TypeConverterTestData(
            python_type=str,
            postgres_type="text",
            postgres_value="'value'",
            python_value="value",
        ),
    ],
}

#
# async def test_all_supported_types_exist_in_test_cases() -> None:
#     unique_python_types: set[type[object]] = set()
#     unique_postgres_types = set()
#     for test_case in SUPPORTED_TYPES_TEST_CASES:
#         unique_python_types.add(test_case)
#         unique_postgres_types.add(test_case.postgres_type)
#
#     assert unique_python_types == SUPPORTED_PYTHON_TYPES
#     assert unique_postgres_types == SUPPORTED_POSTGRES_TYPES
#
#
# ALL_SUPPORTED_POSTGRES_TYPES


@pytest.mark.parametrize(
    ("test_case"),
    [
        (test_case)
        for supported_type in ALL_SUPPORTED_POSTGRES_TYPES
        if supported_type in SUPPORTED_TYPES_TEST_DATA
        for test_case in SUPPORTED_TYPES_TEST_DATA[supported_type]
    ],
)
async def test_all_supported_types_converts(
    asyncpg_connection_pool_to_test_db: Pool, test_case: TypeConverterTestData
) -> None:
    class Model(BaseModel):  # type:ignore[explicit-any]
        a: test_case.python_type  # type:ignore[name-defined] # mypy wtf

    async with asyncpg_connection_pool_to_test_db.acquire() as pool:
        record = await pool.fetchrow(
            query=f"select ({test_case.postgres_value})::{test_case.postgres_type} as a"
        )

        assert record is not None

        assert convert_record_to_pydantic_model(
            record=record, pydantic_model_type=Model
        ) == Model(a=test_case.python_value)


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
        (test_data)
        for supported_type in ALL_SUPPORTED_POSTGRES_TYPES
        if supported_type in SUPPORTED_TYPES_TEST_DATA
        for test_data in SUPPORTED_TYPES_TEST_DATA[supported_type]
    ],
)
async def test_array_converts(
    asyncpg_connection_pool_to_test_db: Pool,
    test_data: TypeConverterTestData,
    test_case: ArrayTestCases,
) -> None:
    expected_python_value: object
    match test_case:
        case ArrayTestCases.None_:
            query_literal = f"(null)::{test_data.postgres_type}[]"
            expected_python_value = None
        case ArrayTestCases.ArrayOfNone:
            query_literal = f"(ARRAY[null])::{test_data.postgres_type}[]"
            expected_python_value = [None]
        case ArrayTestCases.ArrayOfArraysOfNone:
            query_literal = (
                f"(ARRAY[ARRAY[null],ARRAY[null]])::{test_data.postgres_type}[]"
            )
            expected_python_value = [[None], [None]]
        case ArrayTestCases.Array:
            query_literal = (
                f"(ARRAY[{test_data.postgres_value}])::{test_data.postgres_type}[]"
            )
            expected_python_value = [test_data.python_value]
        case ArrayTestCases.ArrayOfArrays:
            query_literal = f"(ARRAY[ARRAY[{test_data.postgres_value}],ARRAY[{test_data.postgres_value}]])::{test_data.postgres_type}[]"
            expected_python_value = [[test_data.python_value], [test_data.python_value]]
        case ArrayTestCases.ArrayOfArraysOfArrays:
            query_literal = f"(ARRAY[ARRAY[ARRAY[{test_data.postgres_value}]],ARRAY[array[{test_data.postgres_value}]]])::{test_data.postgres_type}[]"
            expected_python_value = [
                [[test_data.python_value]],
                [[test_data.python_value]],
            ]
        case _:
            assert_never(test_case)

    RecursiveListDt = TypeAliasType(
        "RecursiveListDt",
        value=typing.Union[
            list[test_data.python_type | None], list["RecursiveListDt"], None  # type: ignore[misc,name-defined] # mypy does not know python type
        ],
    )

    class Model(BaseModel):  # type:ignore[explicit-any]
        a: RecursiveListDt  # type: ignore[valid-type]

    async with asyncpg_connection_pool_to_test_db.acquire() as pool:
        record = await pool.fetchrow(query=f"select {query_literal} as a")

        assert record is not None

        assert convert_record_to_pydantic_model(
            record=record, pydantic_model_type=Model
        ) == Model(a=expected_python_value)


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
