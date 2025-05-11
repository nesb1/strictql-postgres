from asyncpg import Connection


async def delete_users(connection: Connection) -> str:
    query = """
    DELETE FROM users
"""
    return await connection.execute(query)
