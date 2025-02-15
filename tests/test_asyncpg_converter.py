import dataclasses

import asyncpg
import pytest
from pydantic import BaseModel

from asyncpg import Pool
from strictql_postgres.asyncpg_result_converter import (
    convert_records_to_pydantic_models,
)


async def test_asyncpg_converter(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
) -> None:
    records = await asyncpg_connection_pool_to_test_db.fetch(
        "select 1 as a, 'kek' as b"
    )

    class Model(BaseModel):
        a: int
        b: str

    assert convert_records_to_pydantic_models(
        records=records, pydantic_model_type=Model
    ) == [Model(a=1, b="kek")]


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
    python_type: object
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
    unique_python_types = set()
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
    async with asyncpg_connection_pool_to_test_db.acquire() as pool:
        await pool.execute(f"create table test (a {test_case.postgres_type})")

        await pool.execute(
            f"insert into test (a) values ({test_case.postgres_value_as_str})"
        )

        records = await pool.fetch(query="select * from test")

        class Model(BaseModel):
            a: test_case.python_type

        assert convert_records_to_pydantic_models(
            records=records, pydantic_model_type=Model
        ) == [Model(a=test_case.python_value)]
