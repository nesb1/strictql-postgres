from datetime import timedelta

from pydantic import BaseModel

from asyncpg import Connection
from strictql_postgres.api import convert_record_to_pydantic_model


class FetchUserModel(BaseModel):  # type: ignore[explicit-any]
    id: int | None
    name: str | None


async def fetch_user(
    connection: Connection, timeout: timedelta | None = None
) -> FetchUserModel | None:
    query = """
    SELECT *
FROM users
LIMIT 1
"""
    record = await connection.fetchrow(
        query, timeout=timeout.total_seconds() if timeout is not None else None
    )
    if record is None:
        return None
    return convert_record_to_pydantic_model(
        record=record, pydantic_model_type=FetchUserModel
    )
