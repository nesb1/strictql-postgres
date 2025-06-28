import dataclasses
import datetime
import decimal
import inspect
import types
from collections.abc import Sequence

import pydantic
import pytest

import asyncpg
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.queries_to_generate import Parameter
from strictql_postgres.query_generator import (
    QueryToGenerate,
    generate_query_python_code,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.supported_postgres_types import (
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)


@dataclasses.dataclass
class TypeTestData:
    bind_param_cast: str
    value: object


TEST_DATA_FOR_SIMPLE_TYPES: dict[SupportedPostgresSimpleTypes, TypeTestData] = {
    SupportedPostgresSimpleTypes.SMALLINT: TypeTestData(
        bind_param_cast="smallint",
        value=1,
    ),
    SupportedPostgresSimpleTypes.INTEGER: TypeTestData(
        bind_param_cast="integer",
        value=1,
    ),
    SupportedPostgresSimpleTypes.BIGINT: TypeTestData(
        bind_param_cast="bigint",
        value=1,
    ),
    SupportedPostgresSimpleTypes.REAL: TypeTestData(
        bind_param_cast="real",
        value=1.2,
    ),
    SupportedPostgresSimpleTypes.DOUBLE_PRECISION: TypeTestData(
        bind_param_cast="double precision",
        value=2.1,
    ),
    SupportedPostgresSimpleTypes.VARCHAR: TypeTestData(
        bind_param_cast="varchar", value="kek"
    ),
    SupportedPostgresSimpleTypes.CHAR: TypeTestData(
        bind_param_cast="char(3)", value="kek"
    ),
    SupportedPostgresSimpleTypes.BPCHAR: TypeTestData(
        bind_param_cast="bpchar", value="kek"
    ),
    SupportedPostgresSimpleTypes.TEXT: TypeTestData(
        bind_param_cast="text", value="kek"
    ),
}


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (test_case.bind_param_cast, test_case.value)
        for postgres_type, test_case in TEST_DATA_FOR_SIMPLE_TYPES.items()
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
        query_to_generate=QueryToGenerate(
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


TEST_DATA_FOR_TYPES_WITH_IMPORT: dict[
    SupportedPostgresTypeRequiredImports, TypeTestData
] = {
    SupportedPostgresTypeRequiredImports.NUMERIC: TypeTestData(
        bind_param_cast="numeric",
        value=decimal.Decimal("1.012"),
    ),
    SupportedPostgresTypeRequiredImports.DECIMAL: TypeTestData(
        bind_param_cast="numeric",
        value=decimal.Decimal("1.012"),
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMP: TypeTestData(
        bind_param_cast="timestamp",
        value=datetime.datetime(year=2021, month=1, day=1, hour=1, minute=1, second=1),
    ),
    SupportedPostgresTypeRequiredImports.TIMESTAMPTZ: TypeTestData(
        bind_param_cast="timestamptz",
        value=datetime.datetime(
            year=2021,
            month=1,
            day=1,
            hour=1,
            minute=1,
            second=1,
            tzinfo=datetime.timezone.utc,
        ),
    ),
    SupportedPostgresTypeRequiredImports.TIME: TypeTestData(
        bind_param_cast="time",
        value=datetime.time(hour=1, minute=1, second=1),
    ),
    SupportedPostgresTypeRequiredImports.TIMETZ: TypeTestData(
        bind_param_cast="timetz",
        value=datetime.time(hour=1, minute=1, second=1, tzinfo=datetime.timezone.utc),
    ),
    SupportedPostgresTypeRequiredImports.DATE: TypeTestData(
        bind_param_cast="date",
        value=datetime.date(year=2021, month=1, day=1),
    ),
    SupportedPostgresTypeRequiredImports.INTERVAL: TypeTestData(
        bind_param_cast="interval",
        value=datetime.timedelta(days=1),
    ),
}


@pytest.mark.parametrize(
    ("bind_param_cast", "param"),
    [
        (
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].bind_param_cast,
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
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
        query_to_generate=QueryToGenerate(
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
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].bind_param_cast,
            TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].value,
        )
        for data_type in SupportedPostgresTypeRequiredImports
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
        query_to_generate=QueryToGenerate(
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
