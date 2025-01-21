import pathlib

from strictql_postgres.code_generator import (
    generate_code_for_query,
    QueryWithDBInfo,
)
from asyncpg import Pool
from strictql_postgres.code_quality import CodeQualityImprover

from tests.code_generator.expected_generated_code.simple_pydantic_v1 import Model

EXPECTED_GENERATED_CODE_DIR = pathlib.Path(__file__).parent / "expected_generated_code"


async def test_code_generator_pydantic_v1(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeQualityImprover
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = "SELECT * FROM users;"

    from tests.code_generator.expected_generated_code.simple_pydantic_v1 import (
        fetch_all_users,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2)",
        1,
        "kek",
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        users = await fetch_all_users(conn)
        assert users == [Model(id=1, name="kek")]

    with (EXPECTED_GENERATED_CODE_DIR / "simple_pydantic_v1.py").open() as file:
        expected_generated_code = file.read()

    db_row_model = {"id": int, "name": str}

    actual_generated_code = await generate_code_for_query(
        query_with_db_info=QueryWithDBInfo(
            query=query, query_result_row_model=db_row_model
        ),
        execution_variant="fetch_all",
        function_name="fetch_all_users",
        code_quality_improver=code_quality_improver,
    )

    assert actual_generated_code == expected_generated_code
