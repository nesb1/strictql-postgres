from asyncpg.connection import Connection
from asyncpg.prepared_stmt import PreparedStatement

from asyncpg import Record

class PoolAcquireContext:
    async def __aenter__(self) -> Connection: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...

class Pool:
    async def close(self) -> None: ...
    def acquire(self) -> PoolAcquireContext: ...
    async def execute(
        self, query: str, *args: object, timeout: float | None = None
    ) -> str: ...
    async def fetchrow(
        self,
        query: str,
        *args: object,
        timeout: int | None = None,
        record_class: type[Record] | None = None,
    ) -> Record | None: ...
    async def fetch(
        self,
        query: str,
        *args: object,
        timeout: int | None = None,
        record_class: type[Record] | None = None,
    ) -> list[Record]: ...
    async def prepare(
        self,
        query: str,
        *,
        name: str | None = None,
        timeout: int | None = None,
        record_class: type[Record] | None = None,
    ) -> PreparedStatement: ...
    async def __aenter__(self) -> "Pool": ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...

def create_pool(
    dsn: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    max_queries: int | None = None,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    database: str | None = None,
) -> Pool: ...
