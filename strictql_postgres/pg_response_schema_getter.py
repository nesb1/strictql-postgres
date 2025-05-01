import dataclasses
from typing import Mapping

import asyncpg.prepared_stmt
from strictql_postgres.common_types import ColumnType
from strictql_postgres.python_types import ALL_TYPES, SimpleType, SimpleTypes

PgResponseSchema = dict[str, ColumnType]


@dataclasses.dataclass
class PgResponseSchemaTypeNotSupportedError(Exception):
    postgres_type: str
    column_name: str


_PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES = {
    "int2": SimpleTypes.INT,
    "int4": SimpleTypes.INT,
    "int8": SimpleTypes.INT,
    "float4": SimpleTypes.FLOAT,
    "float8": SimpleTypes.FLOAT,
    "varchar": SimpleTypes.STR,
    "char": SimpleTypes.STR,
    "bpchar": SimpleTypes.STR,
    "text": SimpleTypes.STR,
}


def get_pg_response_schema_from_prepared_statement(
    prepared_stmt: asyncpg.prepared_stmt.PreparedStatement,
) -> Mapping[str, ALL_TYPES]:
    pg_response_schema = {}
    for attribute in prepared_stmt.get_attributes():
        try:
            python_type = _PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES[attribute.type.name]
        except KeyError:
            raise PgResponseSchemaTypeNotSupportedError(
                postgres_type=attribute.type.name,
                column_name=attribute.name,
            )
        pg_response_schema[attribute.name] = SimpleType(
            type_=python_type, is_optional=True
        )
    return pg_response_schema
