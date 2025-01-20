from contextlib import asynccontextmanager
from typing import AsyncIterator

import asyncpg


@asynccontextmanager
async def async_pg_connection_context_manager(
    connection_url: str,
) -> AsyncIterator[asyncpg.Pool]:
    connection_pool = await asyncpg.create_pool(dsn=connection_url)
    try:
        yield connection_pool
    finally:
        await connection_pool.close()
