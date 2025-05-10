import dataclasses
from typing import Literal, Sequence

from asyncpg.prepared_stmt import PreparedStatement
from strictql_postgres.python_types import ALL_TYPES, SimpleType
from strictql_postgres.supported_postgres_types import (
    PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES,
    PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT,
)


@dataclasses.dataclass()
class BindParamType:
    type_: type[object]
    is_optional: Literal[True] = True


@dataclasses.dataclass
class PgBindParamTypeNotSupportedError(Exception):
    postgres_type: str

    def __str__(self) -> str:
        return f"Postgres type '{self.postgres_type}' not supported"


async def get_bind_params_python_types(
    prepared_statement: PreparedStatement,
) -> Sequence[ALL_TYPES]:
    parameters = prepared_statement.get_parameters()

    parameters_python_types: list[ALL_TYPES] = []
    for param in parameters:
        simple_type = PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES.get(param.name)
        if simple_type is not None:
            parameters_python_types.append(
                SimpleType(type_=simple_type, is_optional=True)
            )
            continue
        type_ = PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT.get(param.name)

        if type_ is not None:
            parameters_python_types.append(type_(is_optional=True))
            continue

        raise PgBindParamTypeNotSupportedError(postgres_type=param.name)

    return parameters_python_types
