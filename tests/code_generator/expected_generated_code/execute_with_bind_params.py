from asyncpg import Connection


async def delete_users(connection: Connection, id: int | None, name: str | None) -> str:
    query = """
    DELETE FROM users
WHERE id = $1
  AND name = $2
"""
    return await connection.execute(query, id, name)
