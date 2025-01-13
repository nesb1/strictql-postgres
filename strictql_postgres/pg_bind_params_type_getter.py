import dataclasses
from typing import Literal

from asyncpg.prepared_stmt import PreparedStatement


@dataclasses.dataclass()
class BindParamType:
    type_: type[object]
    is_optional: Literal[True] = True


@dataclasses.dataclass
class PgBindParamTypeNotSupportedError(Exception):
    postgres_type: str


async def get_bind_params_python_types(
    prepared_statement: PreparedStatement,
    python_type_by_postgres_type: dict[str, type[object]],
) -> list[BindParamType]:
    parameters = prepared_statement.get_parameters()

    parameters_python_types = []
    for param in parameters:
        try:
            python_type = python_type_by_postgres_type[param.name]
        except KeyError:
            raise PgBindParamTypeNotSupportedError(postgres_type=param.name)
        parameters_python_types.append(
            BindParamType(type_=python_type, is_optional=True)
        )
    return parameters_python_types
