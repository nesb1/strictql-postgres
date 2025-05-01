from collections.abc import Sequence
from typing import TypeVar

import pydantic
from pydantic import BaseModel

from asyncpg import Record
from asyncpg.types import Range

T = TypeVar("T", bound=BaseModel)


class RangeType(pydantic.BaseModel):  # type: ignore[explicit-any,misc]
    a: object
    b: object


def convert_records_to_pydantic_models(
    records: Sequence[Record], pydantic_model_type: type[T]
) -> Sequence[T]:
    pydantic_models = []
    model_dict: dict[str, object] = {}

    for record in records:
        for field_name, field_value in record.items():
            if isinstance(field_value, Range):
                model_dict[field_name] = RangeType(
                    a=field_value.lower, b=field_value.upper
                )
            else:
                model_dict[field_name] = field_value

        pydantic_models.append(pydantic_model_type.model_validate(model_dict))

    return pydantic_models
