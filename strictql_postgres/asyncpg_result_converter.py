from collections.abc import Sequence
from typing import TypeVar

import pydantic
from pydantic import BaseModel

from asyncpg import Record
from asyncpg.types import Range

T = TypeVar("T", bound=BaseModel)


class RangeType(pydantic.BaseModel):  # type: ignore[explicit-any]
    a: object
    b: object


def convert_record_to_pydantic_model(record: Record, pydantic_model_type: type[T]) -> T:
    model_dict: dict[str, object] = {}
    for field_name, field_value in record.items():
        if isinstance(field_value, Range):
            model_dict[field_name] = RangeType(a=field_value.lower, b=field_value.upper)
        else:
            model_dict[field_name] = field_value
    return pydantic_model_type.model_validate(model_dict)


def convert_records_to_pydantic_models(
    records: Sequence[Record], pydantic_model_type: type[T]
) -> Sequence[T]:
    pydantic_models = []

    for record in records:
        pydantic_models.append(
            convert_record_to_pydantic_model(
                record=record, pydantic_model_type=pydantic_model_type
            )
        )

    return pydantic_models
