import dataclasses
from typing import Literal, Sequence

from asyncpg.prepared_stmt import PreparedStatement
from strictql_postgres.python_types import ALL_TYPES, SimpleType
from strictql_postgres.supported_postgres_types import (
    PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES,
)


@dataclasses.dataclass()
class BindParamType:
    type_: type[object]
    is_optional: Literal[True] = True


@dataclasses.dataclass
class PgBindParamTypeNotSupportedError(Exception):
    postgres_type: str


async def get_bind_params_python_types(
    prepared_statement: PreparedStatement,
) -> Sequence[ALL_TYPES]:
    parameters = prepared_statement.get_parameters()

    parameters_python_types = []
    for param in parameters:
        type_ = PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES.get(param.name)
        if type_ is not None:
            parameters_python_types.append(SimpleType(type_=type_, is_optional=True))
    return parameters_python_types
