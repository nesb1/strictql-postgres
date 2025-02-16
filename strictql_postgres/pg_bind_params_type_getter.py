import dataclasses

from asyncpg.prepared_stmt import PreparedStatement


QueryParamType = type[object]


@dataclasses.dataclass
class BindParamTypeNotSupportedError(Exception):
    postgres_type: str


def get_bind_params_python_types_from_prepared_statement(
    prepared_statement: PreparedStatement,
    python_type_by_postgres_type: dict[str, type[object]],
) -> list[QueryParamType]:
    parameters = prepared_statement.get_parameters()

    parameters_python_types = []
    for param in parameters:
        try:
            python_type = python_type_by_postgres_type[param.name]
        except KeyError:
            raise BindParamTypeNotSupportedError(postgres_type=param.name)
        parameters_python_types.append(python_type)
    return parameters_python_types
