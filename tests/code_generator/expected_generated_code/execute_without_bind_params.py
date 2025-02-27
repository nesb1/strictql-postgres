from asyncpg import Connection


async def delete_users(connection: Connection) -> str:
    return await connection.execute("delete from users;")
