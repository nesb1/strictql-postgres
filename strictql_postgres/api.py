from typing import TypeVar, Type, Sequence

import asyncpg
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


async def fetch_rows_with_pydantic_model(
    connection: asyncpg.Connection,
    model: Type[T],
    query: str,
    params: dict[str, object] | None = None,
) -> Sequence[T]:
    raise NotImplementedError()
