import dataclasses

import asyncpg
from asyncpg.prepared_stmt import PreparedStatement
from pglast.ast import RawStmt, InsertStmt, SetToDefault
from pglast import parse_sql

from strictql_postgres.table_field_getter import get_table_fields


@dataclasses.dataclass()
class BindParamType:
    type_: type[object]
    is_optional: bool


@dataclasses.dataclass
class PgBindParamTypeNotSupportedError(Exception):
    postgres_type: str


async def get_bind_params_python_types(
    prepared_statement: PreparedStatement,
    python_type_by_postgres_type: dict[str, type[object]],
    parsed_sql: tuple[RawStmt, ...],
    make_bind_params_more_optional: bool,
    connection: asyncpg.connection.Connection,
) -> list[BindParamType]:
    parameters = prepared_statement.get_parameters()
    stmt = parsed_sql[0].stmt
    if isinstance(stmt, InsertStmt):
        if stmt.relation is None:
            raise NotImplementedError("Not supported insert query without relation")
        table_name = stmt.relation.relname
        columns_in_insert_statement = [col.name for col in stmt.cols]
        fields = await get_table_fields(connection=connection, table_name=table_name)
        indexes_of_values_without_default = []
        for index, value in enumerate(stmt.selectStmt.valuesLists):
            if isinstance(value, SetToDefault):
                continue
            indexes_of_values_without_default.append(index)

        bind_params = []
        for index, col in enumerate(columns_in_insert_statement):
            if index not in indexes_of_values_without_default:
                continue
            if col not in fields:
                raise NotImplementedError()
            type_ = parameters[index].name
            bind_params.append(
                BindParamType(
                    type_=python_type_by_postgres_type[type_],
                    is_optional=not fields[col].not_null,
                )
            )

        return bind_params

    parameters_python_types = []
    for param in parameters:
        try:
            python_type = python_type_by_postgres_type[param.name]
        except KeyError:
            raise PgBindParamTypeNotSupportedError(postgres_type=param.name)
        parameters_python_types.append(
            BindParamType(type_=python_type, is_optional=make_bind_params_more_optional)
        )
    return parameters_python_types
