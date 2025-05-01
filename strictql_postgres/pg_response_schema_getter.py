import dataclasses
from typing import Mapping

import asyncpg.prepared_stmt
from strictql_postgres.common_types import ColumnType
from strictql_postgres.python_types import (
    ALL_TYPES,
    DecimalType,
    SimpleType,
    SimpleTypes,
    TypesWithImport,
)

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

_PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT: dict[
    str, type[TypesWithImport]
] = {
    "decimal": DecimalType,
    "numeric": DecimalType,
}


def get_pg_response_schema_from_prepared_statement(
    prepared_stmt: asyncpg.prepared_stmt.PreparedStatement,
) -> Mapping[str, ALL_TYPES]:
    pg_response_schema: dict[str, ALL_TYPES] = {}
    for attribute in prepared_stmt.get_attributes():
        python_simple_type = _PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES.get(
            attribute.type.name
        )

        if python_simple_type is not None:
            pg_response_schema[attribute.name] = SimpleType(
                type_=python_simple_type, is_optional=True
            )
            continue

        type_with_import = _PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT.get(
            attribute.type.name
        )

        if type_with_import is not None:
            pg_response_schema[attribute.name] = type_with_import(is_optional=True)
            continue

        raise PgResponseSchemaTypeNotSupportedError(
            postgres_type=attribute.type.name,
            column_name=attribute.name,
        )
    return pg_response_schema
