from asyncio import AbstractEventLoop
from ssl import SSLContext

from asyncpg.prepared_stmt import PreparedStatement

from asyncpg import Record

class Connection:
    async def execute(
        self, query: str, *args: object, timeout: float | None = None
    ) -> str: ...
    async def fetchrow(
        self,
        query: str,
        *args: object,
        timeout: float | None = None,
        record_class: type[Record] | None = None,
    ) -> Record | None: ...
    async def fetch(
        self,
        query: str,
        *args: object,
        timeout: float | None = None,
        record_class: type[Record] | None = None,
    ) -> list[Record]: ...
    async def prepare(
        self,
        query: str,
        *,
        name: str | None = None,
        timeout: float | None = None,
        record_class: type[Record] | None = None,
    ) -> PreparedStatement: ...
    async def close(self) -> None: ...

async def connect(
    dsn: str | None = None,
    *,
    host: str | None = None,
    port: int | None = None,
    user: str | None = None,
    password: str | None = None,
    passfile: str | None = None,
    database: str | None = None,
    loop: AbstractEventLoop | None = None,
    timeout: int = 60,
    statement_cache_size: int = 100,
    max_cached_statement_lifetime: int = 300,
    max_cacheable_statement_size: int = 1024 * 15,
    command_timeout: int | None = None,
    ssl: bool | SSLContext | str | None = None,
    direct_tls: bool = False,
    connection_class: type[Connection] = Connection,
    record_class: type[Record] = Record,
    server_settings: dict[object, object] | None = None,
    target_session_attrs: str | None = None,
) -> Connection: ...
