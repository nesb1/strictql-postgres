from collections.abc import Sequence
from typing import TypeVar

from asyncpg import Record
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def convert_records_to_pydantic_models(
    records: Sequence[Record], pydantic_type: type[T]
) -> Sequence[T]:
    pydantic_models = []
    for record in records:
        pydantic_models.append(pydantic_type.parse_obj(record))

    return pydantic_models
