from asyncpg import Connection


async def delete_users(connection: Connection, id: int, name: str | None) -> str:
    return await connection.execute(
        "delete from users where id = $1 and name = $2;", id, name
    )
