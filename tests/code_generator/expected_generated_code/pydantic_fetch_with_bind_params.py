from pydantic import BaseModel
from asyncpg import Connection
from collections.abc import Sequence

from strictql_postgres.api import convert_records_to_pydantic_models


class FetchAllUsersModel(BaseModel):
    id: int
    name: str


async def fetch_all_users(
    connection: Connection, id: int, name: str
) -> Sequence[FetchAllUsersModel]:
    records = await connection.fetch(
        "SELECT * FROM users where id = $1 and name = $2;", id, name
    )
    return convert_records_to_pydantic_models(
        records=records, pydantic_model_type=FetchAllUsersModel
    )
