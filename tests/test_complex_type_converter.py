import pydantic
import pytest

import asyncpg
from strictql_postgres.complex_type_converter import (
    convert_postgres_complex_type_to_bind_param_value,
)


class SimpleType(pydantic.BaseModel):  # type: ignore[explicit-any]
    a: int
    b: int


class TypeWithOptional(pydantic.BaseModel):  # type: ignore[explicit-any]
    a: int | None


class TypeWithList(pydantic.BaseModel):  # type: ignore[explicit-any]
    l: list[int]  # noqa: E741


class TypeWithInnerList(pydantic.BaseModel):  # type: ignore[explicit-any]
    l: list[SimpleType]  # noqa: E741


class TypeWithInnerInnerList(pydantic.BaseModel):  # type: ignore[explicit-any]
    l: list[TypeWithInnerList]  # noqa: E741


@pytest.mark.parametrize(
    ("complex_type", "type_definition", "sql_literal", "result_like_sql_literal"),
    [
        (
            SimpleType(a=1, b=2),
            "create type ct as (a integer, b integer)",
            "$1::ct",
            "(1,2)::ct",
        ),
        (
            TypeWithOptional(a=None),
            "create type ct as (a integer)",
            "$1::ct",
            "row(null)::ct",
        ),
        (
            TypeWithList(l=[1, 2, 3]),
            "create type ct as (l integer[])",
            "$1::ct",
            "row(array[1,2,3])::ct",
        ),
        (
            TypeWithInnerList(l=[SimpleType(a=1, b=2), SimpleType(a=2, b=1)]),
            "create type inner_type as (a integer, b integer); create type ct as (l inner_type[])",
            "$1::ct",
            "row(array[row(1,2)::inner_type,row(2,1)::inner_type])::ct",
        ),
        (
            TypeWithInnerInnerList(
                l=[
                    TypeWithInnerList(l=[SimpleType(a=1, b=2), SimpleType(a=2, b=1)]),
                    TypeWithInnerList(l=[SimpleType(a=0, b=0), SimpleType(a=1, b=1)]),
                ]
            ),
            "create type inner_type as (a integer, b integer); create type inner_list_type as (l inner_type[]);create type ct as (l inner_list_type[])",
            "$1::ct",
            "row(array[row(array[row(1,2)::inner_type,row(2,1)::inner_type])::inner_list_type,row(array[row(0,0)::inner_type,row(1,1)::inner_type])::inner_list_type])::ct",
        ),
    ],
)
async def test_convert(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    complex_type: pydantic.BaseModel,
    type_definition: str,
    sql_literal: str,
    result_like_sql_literal: str,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute(type_definition)
        converted_comples_type = convert_postgres_complex_type_to_bind_param_value(
            complex_type=complex_type
        )
        actual_result = await connection.fetch(
            f"select {sql_literal} as value", converted_comples_type
        )
        expected_result = await connection.fetch(
            f"select {result_like_sql_literal} as value"
        )

        assert actual_result == expected_result
