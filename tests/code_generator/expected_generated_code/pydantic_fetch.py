from pydantic import BaseModel
from asyncpg import Connection
from collections.abc import Sequence

from strictql_postgres.api import convert_records_to_pydantic_models


class Model(BaseModel):
    id: int
    name: str


async def fetch_all_users(connection: Connection) -> Sequence[Model]:
    records = await connection.fetch("SELECT * FROM users;")
    return convert_records_to_pydantic_models(
        records=records, pydantic_model_type=Model
    )
