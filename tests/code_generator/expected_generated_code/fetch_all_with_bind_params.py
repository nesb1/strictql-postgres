from collections.abc import Sequence
from datetime import timedelta

from pydantic import BaseModel

from asyncpg import Connection
from strictql_postgres.api import convert_records_to_pydantic_models


class FetchAllUsersModel(BaseModel):  # type: ignore[explicit-any]
    id: int | None
    name: str | None


async def fetch_all_users(
    connection: Connection,
    id: int | None,
    name: str | None,
    timeout: timedelta | None = None,
) -> Sequence[FetchAllUsersModel]:
    query = """
    SELECT *
FROM users
WHERE id = $1
  AND name = $2
"""
    records = await connection.fetch(
        query,
        id,
        name,
        timeout=timeout.total_seconds() if timeout is not None else None,
    )
    return convert_records_to_pydantic_models(
        records=records, pydantic_model_type=FetchAllUsersModel
    )
