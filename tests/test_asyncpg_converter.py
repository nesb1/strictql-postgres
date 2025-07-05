import dataclasses

import pytest
from pydantic import BaseModel

import asyncpg
from asyncpg import Pool
from strictql_postgres.asyncpg_result_converter import (
    RangeType,
    convert_record_to_pydantic_model,
)


async def test_asyncpg_converter(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    record = await asyncpg_connection_pool_to_test_db.fetchrow(
        "select 1 as a, 'kek' as b"
    )

    class Model(BaseModel):  # type:ignore[explicit-any]
        a: int
        b: str

    assert record is not None

    assert convert_record_to_pydantic_model(
        record=record, pydantic_model_type=Model
    ) == Model(a=1, b="kek")


SUPPORTED_PYTHON_TYPES = {
    int,
    str,
    # bool,
    # datetime.datetime,
    # datetime.date,
    # datetime.time,
    # float,
    # Decimal,
}

SUPPORTED_POSTGRES_TYPES = {"varchar", "integer", "text"}


@dataclasses.dataclass
class TypeConverterTestCase:
    python_type: type[object]
    postgres_type: str
    postgres_value_as_str: str
    python_value: object


SUPPORTED_TYPES_TEST_CASES = [
    TypeConverterTestCase(
        python_type=int,
        postgres_type="integer",
        postgres_value_as_str="1",
        python_value=1,
    ),
    TypeConverterTestCase(
        python_type=int,
        postgres_type="integer",
        postgres_value_as_str="0",
        python_value=0,
    ),
    TypeConverterTestCase(
        python_type=int,
        postgres_type="integer",
        postgres_value_as_str="-1",
        python_value=-1,
    ),
    TypeConverterTestCase(
        python_type=str,
        postgres_type="varchar",
        postgres_value_as_str="'value'",
        python_value="value",
    ),
    TypeConverterTestCase(
        python_type=str,
        postgres_type="text",
        postgres_value_as_str="'value'",
        python_value="value",
    ),
]


async def test_all_supported_types_exist_in_test_cases() -> None:
    unique_python_types: set[type[object]] = set()
    unique_postgres_types = set()
    for test_case in SUPPORTED_TYPES_TEST_CASES:
        unique_python_types.add(test_case.python_type)
        unique_postgres_types.add(test_case.postgres_type)

    assert unique_python_types == SUPPORTED_PYTHON_TYPES
    assert unique_postgres_types == SUPPORTED_POSTGRES_TYPES


@pytest.mark.parametrize(("test_case"), [*SUPPORTED_TYPES_TEST_CASES])
async def test_all_supported_types_converts(
    asyncpg_connection_pool_to_test_db: Pool, test_case: TypeConverterTestCase
) -> None:
    class Model(BaseModel):  # type:ignore[explicit-any]
        a: test_case.python_type  # type:ignore[name-defined] # mypy wtf

    async with asyncpg_connection_pool_to_test_db.acquire() as pool:
        await pool.execute(f"create table test (a {test_case.postgres_type})")

        await pool.execute(
            f"insert into test (a) values ({test_case.postgres_value_as_str})"
        )

        record = await pool.fetchrow(query="select * from test")
        assert record is not None

        assert convert_record_to_pydantic_model(
            record=record, pydantic_model_type=Model
        ) == Model(a=test_case.python_value)


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
