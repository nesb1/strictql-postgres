from collections.abc import Sequence
from typing import TypeVar

from pydantic import BaseModel

from asyncpg import Record

T = TypeVar("T", bound=BaseModel)


def convert_records_to_pydantic_models(
    records: Sequence[Record], pydantic_model_type: type[T]
) -> Sequence[T]:
    pydantic_models = []
    for record in records:
        model_dict: dict[str, object] = dict(record.items())
        pydantic_models.append(pydantic_model_type.model_validate(model_dict))

    return pydantic_models
