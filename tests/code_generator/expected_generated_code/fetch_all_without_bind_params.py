from collections.abc import Sequence

from pydantic import BaseModel

from asyncpg import Connection
from strictql_postgres.api import convert_records_to_pydantic_models


class FetchAllUsersModel(BaseModel):  # type: ignore[explicit-any,misc]
    id: int | None
    name: str | None


async def fetch_all_users(connection: Connection) -> Sequence[FetchAllUsersModel]:
    query = """
    SELECT *
FROM users
"""
    records = await connection.fetch(query)
    return convert_records_to_pydantic_models(
        records=records, pydantic_model_type=FetchAllUsersModel
    )
