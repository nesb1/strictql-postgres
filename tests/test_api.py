import datetime
from decimal import Decimal

from asyncpg import Pool
from strictql_postgres.api import fetch_rows_with_pydantic_model
from pydantic import BaseModel


async def test_fetch_rows_with_pydantic_model_works(
    asyncpg_connection_pool_to_test_db: Pool,
):
    class Model(BaseModel):
        id: int

    async with asyncpg_connection_pool_to_test_db.acquire() as connection:
        await connection.execute("create table test (id int);")

        await connection.execute("insert into test (id) values (1),(2),(3);")

        expected_response = [
            Model(id=1),
            Model(id=2),
        ]

        actual_response = await fetch_rows_with_pydantic_model(
            connection=connection,
            model=Model,
            query="SELECT * FROM test where id < $1",
        )

        assert actual_response == expected_response


"""
добавить параметры в запрос

подумать над интерфейсом для передачи параметров
"""
