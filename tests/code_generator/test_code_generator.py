import pathlib

from asyncpg import Pool
from pglast import prettify
from strictql_postgres.code_generator import (
    generate_code_for_query_with_execute_method,
    generate_code_for_query_with_fetch_all_method,
    generate_code_for_query_with_fetch_row_method,
)
from strictql_postgres.code_quality import CodeFixer
from strictql_postgres.common_types import (
    BindParam,
    NotEmptyRowSchema,
)
from strictql_postgres.python_types import (
    Integer,
    SimpleTypes,
    String,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from tests.code_generator.expected_generated_code.fetch_all_with_bind_params import (
    FetchAllUsersModel as FetchAllUsersModelWithBindParams,
)
from tests.code_generator.expected_generated_code.fetch_all_without_bind_params import (
    FetchAllUsersModel as FetchAllUsersModelWithoutBindParams,
)
from tests.code_generator.expected_generated_code.fetch_row_with_bind_params import (
    FetchUserModel as FetchUserModelWithBindParams,
)
from tests.code_generator.expected_generated_code.fetch_row_without_bind_params import (
    FetchUserModel as FetchUserModelWithoutBindParams,
)

EXPECTED_GENERATED_CODE_DIR = pathlib.Path(__file__).parent / "expected_generated_code"


async def test_code_generator_fetch_all_without_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeFixer
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = prettify("SELECT * FROM users;")

    from tests.code_generator.expected_generated_code.fetch_all_without_bind_params import (
        fetch_all_users,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2)",
        1,
        "kek",
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        users = await fetch_all_users(conn)
        assert list(users) == [FetchAllUsersModelWithoutBindParams(id=1, name="kek")]

    with (
        EXPECTED_GENERATED_CODE_DIR / "fetch_all_without_bind_params.py"
    ).open() as file:
        expected_generated_code = file.read()

    db_row_model: dict[str, SimpleTypes] = {
        "id": Integer(is_optional=True),
        "name": String(is_optional=True),
    }

    actual_generated_code = await generate_code_for_query_with_fetch_all_method(
        query=query,
        result_schema=NotEmptyRowSchema(db_row_model),
        bind_params=[],
        function_name=StringInSnakeLowerCase("fetch_all_users"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code


async def test_code_generator_pydantic_with_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeFixer
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = prettify("SELECT * FROM users where id = $1 and name = $2;")

    from tests.code_generator.expected_generated_code.fetch_all_with_bind_params import (
        fetch_all_users,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2), ($3, $4)", 1, "kek", 2, "kek2"
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        users = await fetch_all_users(conn, id=1, name="kek")
        assert list(users) == [FetchAllUsersModelWithBindParams(id=1, name="kek")]

    with (EXPECTED_GENERATED_CODE_DIR / "fetch_all_with_bind_params.py").open() as file:
        expected_generated_code = file.read()

    db_row_model: dict[str, SimpleTypes] = {
        "id": Integer(is_optional=True),
        "name": String(is_optional=True),
    }

    actual_generated_code = await generate_code_for_query_with_fetch_all_method(
        query=query,
        result_schema=NotEmptyRowSchema(db_row_model),
        bind_params=[
            BindParam(
                name_in_function="id",
                type_=Integer(is_optional=True),
            ),
            BindParam(
                name_in_function="name",
                type_=String(is_optional=True),
            ),
        ],
        function_name=StringInSnakeLowerCase("fetch_all_users"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code


async def test_code_generator_fetch_row_without_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeFixer
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = prettify("SELECT * FROM users limit 1;")

    from tests.code_generator.expected_generated_code.fetch_row_without_bind_params import (
        fetch_user,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2)",
        1,
        "kek",
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        user = await fetch_user(conn)
        assert user == FetchUserModelWithoutBindParams(id=1, name="kek")

    with (
        EXPECTED_GENERATED_CODE_DIR / "fetch_row_without_bind_params.py"
    ).open() as file:
        expected_generated_code = file.read()

    db_row_model: dict[str, SimpleTypes] = {
        "id": Integer(is_optional=True),
        "name": String(is_optional=True),
    }

    actual_generated_code = await generate_code_for_query_with_fetch_row_method(
        query=query,
        result_schema=NotEmptyRowSchema(db_row_model),
        bind_params=[],
        function_name=StringInSnakeLowerCase("fetch_user"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code


async def test_code_generator_fetch_row_pydantic_with_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeFixer
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = prettify("SELECT * FROM users where id = $1 and name = $2 limit 1;")

    from tests.code_generator.expected_generated_code.fetch_row_with_bind_params import (
        fetch_user,
    )

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2), ($3, $4)", 1, "kek", 2, "kek2"
    )
    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        user = await fetch_user(conn, id=1, name="kek")
        assert user == FetchUserModelWithBindParams(id=1, name="kek")

    with (EXPECTED_GENERATED_CODE_DIR / "fetch_row_with_bind_params.py").open() as file:
        expected_generated_code = file.read()

    db_row_model: dict[str, SimpleTypes] = {
        "id": Integer(is_optional=True),
        "name": String(is_optional=True),
    }

    actual_generated_code = await generate_code_for_query_with_fetch_row_method(
        query=query,
        result_schema=NotEmptyRowSchema(db_row_model),
        bind_params=[
            BindParam(
                name_in_function="id",
                type_=Integer(is_optional=True),
            ),
            BindParam(
                name_in_function="name",
                type_=String(is_optional=True),
            ),
        ],
        function_name=StringInSnakeLowerCase("fetch_user"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code


async def test_code_generator_execute_with_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeFixer
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = "delete from users where id = $1 and name = $2;"

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2), ($3, $4)", 1, "kek", 2, "kek2"
    )
    from tests.code_generator.expected_generated_code.execute_with_bind_params import (
        delete_users,
    )

    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        delete_users_result = await delete_users(conn, id=1, name="kek")
        assert delete_users_result == "DELETE 1"

    with (EXPECTED_GENERATED_CODE_DIR / "execute_with_bind_params.py").open() as file:
        expected_generated_code = file.read()

    actual_generated_code = await generate_code_for_query_with_execute_method(
        query=query,
        bind_params=[
            BindParam(
                name_in_function="id",
                type_=Integer(is_optional=True),
            ),
            BindParam(
                name_in_function="name",
                type_=String(is_optional=True),
            ),
        ],
        function_name=StringInSnakeLowerCase("delete_users"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code


async def test_code_generator_execute_without_bind_params(
    asyncpg_connection_pool_to_test_db: Pool, code_quality_improver: CodeFixer
) -> None:
    await asyncpg_connection_pool_to_test_db.execute(
        "create table users (id serial not null, name text)"
    )

    query = "delete from users;"

    await asyncpg_connection_pool_to_test_db.execute(
        "insert into users (id, name) values ($1, $2), ($3, $4)", 1, "kek", 2, "kek2"
    )
    from tests.code_generator.expected_generated_code.execute_without_bind_params import (
        delete_users,
    )

    async with asyncpg_connection_pool_to_test_db.acquire() as conn:
        delete_users_result = await delete_users(conn)
        assert delete_users_result == "DELETE 2"

    with (
        EXPECTED_GENERATED_CODE_DIR / "execute_without_bind_params.py"
    ).open() as file:
        expected_generated_code = file.read()

    actual_generated_code = await generate_code_for_query_with_execute_method(
        query=query,
        bind_params=[],
        function_name=StringInSnakeLowerCase("delete_users"),
        code_quality_improver=code_quality_improver,
    )
    assert actual_generated_code == expected_generated_code
