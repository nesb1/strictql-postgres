import dataclasses

import pytest

import asyncpg
from strictql_postgres.pg_bind_params_type_getter import (
    get_bind_params_python_types,
)
from strictql_postgres.python_types import (
    DateTimeType,
    DateType,
    DecimalType,
    SimpleType,
    SimpleTypes,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
)
from strictql_postgres.supported_postgres_types import (
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)


@dataclasses.dataclass
class SimpleTypeTestData:
    bind_param_cast: str
    expected_python_type: SimpleTypes


TEST_DATA_FOR_SIMPLE_TYPES: dict[SupportedPostgresSimpleTypes, SimpleTypeTestData] = {
    SupportedPostgresSimpleTypes.SMALLINT: SimpleTypeTestData(
        bind_param_cast="smallint",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.INTEGER: SimpleTypeTestData(
        bind_param_cast="integer",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.BIGINT: SimpleTypeTestData(
        bind_param_cast="bigint",
        expected_python_type=SimpleTypes.INT,
    ),
    SupportedPostgresSimpleTypes.REAL: SimpleTypeTestData(
        bind_param_cast="real",
        expected_python_type=SimpleTypes.FLOAT,
    ),
    SupportedPostgresSimpleTypes.DOUBLE_PRECISION: SimpleTypeTestData(
        bind_param_cast="double precision",
        expected_python_type=SimpleTypes.FLOAT,
    ),
    SupportedPostgresSimpleTypes.VARCHAR: SimpleTypeTestData(
        bind_param_cast="varchar", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.CHAR: SimpleTypeTestData(
        bind_param_cast="char", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.BPCHAR: SimpleTypeTestData(
        bind_param_cast="bpchar", expected_python_type=SimpleTypes.STR
    ),
    SupportedPostgresSimpleTypes.TEXT: SimpleTypeTestData(
        bind_param_cast="text", expected_python_type=SimpleTypes.STR
    ),
}


@pytest.mark.parametrize(
    ("query_literal", "expected_python_type"),
    [
        (test_case.bind_param_cast, test_case.expected_python_type)
        for postgres_type, test_case in TEST_DATA_FOR_SIMPLE_TYPES.items()
    ],
)
async def test_get_bind_params_types_for_simple_types(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    query_literal: str,
    expected_python_type: SimpleTypes,
) -> None:
    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(
            f"select ($1::{query_literal}) as value"
        )
        actual_bind_params = await get_bind_params_python_types(
            prepared_statement=prepared_statement,
        )

        assert actual_bind_params == [
            SimpleType(type_=expected_python_type, is_optional=True)
        ]


@dataclasses.dataclass
class TypeWithImportTestData:
    bind_param_cast: str
    expected_python_type: type[TypesWithImport]


TEST_DATA_FOR_TYPES_WITH_IMPORT: dict[
    SupportedPostgresTypeRequiredImports, TypeWithImportTestData
] = {
    SupportedPostgresTypeRequiredImports.NUMERIC: TypeWithImportTestData(
        bind_param_cast="numeric",
        expected_python_type=DecimalType,
    ),
    SupportedPostgresTypeRequiredImports.DECIMAL: TypeWithImportTestData(
        bind_param_cast="decimal",
        expected_python_type=DecimalType,
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMP: TypeWithImportTestData(
        bind_param_cast="timestamp",
        expected_python_type=DateTimeType,
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMPTZ: TypeWithImportTestData(
        bind_param_cast="timestamptz",
        expected_python_type=DateTimeType,
    ),
    SupportedPostgresTypeRequiredImports.TIME: TypeWithImportTestData(
        bind_param_cast="time",
        expected_python_type=TimeType,
    ),
    SupportedPostgresTypeRequiredImports.TIMETZ: TypeWithImportTestData(
        bind_param_cast="timetz",
        expected_python_type=TimeType,
    ),
    SupportedPostgresTypeRequiredImports.DATE: TypeWithImportTestData(
        bind_param_cast="date",
        expected_python_type=DateType,
    ),
    SupportedPostgresTypeRequiredImports.INTERVAL: TypeWithImportTestData(
        bind_param_cast="interval",
        expected_python_type=TimeDeltaType,
    ),
}


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].bind_param_cast,
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].expected_python_type,
        )
        for data_type in SupportedPostgresTypeRequiredImports
    ],
)
async def test_generate_code_and_execute_for_types_with_import_in_response_model(
    asyncpg_connection_pool_to_test_db: asyncpg.Pool,
    bind_param_cast: str,
    param: type[TypesWithImport],
) -> None:
    query = f"select ($1::{bind_param_cast}) as value"

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        prepared_statement = await connection.prepare(query)

        actual_bind_params = await get_bind_params_python_types(
            prepared_statement=prepared_statement
        )

        assert actual_bind_params == [param(is_optional=True)]
