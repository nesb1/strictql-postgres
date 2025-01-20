import asyncpg
from pydantic import BaseModel
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

    assert convert_records_to_pydantic_models(records=records, pydantic_type=Model) == [
        Model(a=1, b="kek")
    ]
