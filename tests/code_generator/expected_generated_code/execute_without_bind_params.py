from datetime import timedelta

from asyncpg import Connection


async def delete_users(connection: Connection, timeout: timedelta | None = None) -> str:
    query = """
    DELETE FROM users
"""
    return await connection.execute(
        query, timeout=timeout.total_seconds() if timeout is not None else None
    )
