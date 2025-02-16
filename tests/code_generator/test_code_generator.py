import pathlib

from strictql_postgres.code_generator import (
    generate_code_for_query,
)
from strictql_postgres.common_types import QueryParam, QueryWithDBInfo, SelectQuery
from asyncpg import Pool
from strictql_postgres.code_quality import CodeQualityImprover
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase

from tests.code_generator.expected_generated_code.pydantic_fetch_without_bind_params import (
    FetchAllUsersModel,
)

EXPECTED_GENERATED_CODE_DIR = pathlib.Path(__file__).parent / "expected_generated_code"


async def test_code_generator_pydantic_without_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeQualityImprover
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = "SELECT * FROM users;"

    from tests.code_generator.expected_generated_code.pydantic_fetch_without_bind_params import (
        fetch_all_users,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2)",
        1,
        "kek",
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        users = await fetch_all_users(conn)
        assert list(users) == [FetchAllUsersModel(id=1, name="kek")]

    with (
        EXPECTED_GENERATED_CODE_DIR / "pydantic_fetch_without_bind_params.py"
    ).open() as file:
        expected_generated_code = file.read()

    db_row_model = {"id": int, "name": str}

    actual_generated_code = await generate_code_for_query(
        query_with_db_info=QueryWithDBInfo(
            query=SelectQuery(query=query), result_row_model=db_row_model, params=[]
        ),
        execution_variant="fetch_all",
        function_name=StringInSnakeLowerCase("fetch_all_users"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code


async def test_code_generator_pydantic_with_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeQualityImprover
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = "SELECT * FROM users where id = $1 and name = $2;"

    from tests.code_generator.expected_generated_code.pydantic_fetch_with_bind_params import (
        fetch_all_users,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2), ($3, $4)", 1, "kek", 2, "kek2"
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        users = await fetch_all_users(conn, id=1, name="kek")
        assert list(users) == [FetchAllUsersModel(id=1, name="kek")]

    with (
        EXPECTED_GENERATED_CODE_DIR / "pydantic_fetch_with_bind_params.py"
    ).open() as file:
        expected_generated_code = file.read()

    db_row_model = {"id": int, "name": str}

    actual_generated_code = await generate_code_for_query(
        query_with_db_info=QueryWithDBInfo(
            query=SelectQuery(query=query),
            result_row_model=db_row_model,
            params=[
                QueryParam(name_in_function="id", type_=int),
                QueryParam(name_in_function="name", type_=str),
            ],
        ),
        execution_variant="fetch_all",
        function_name=StringInSnakeLowerCase("fetch_all_users"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code
