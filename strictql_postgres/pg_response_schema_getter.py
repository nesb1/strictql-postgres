import dataclasses
from strictql_postgres.common_types import ColumnType
import asyncpg.prepared_stmt


PgResponseSchema = dict[str, ColumnType]


@dataclasses.dataclass
class PgResponseSchemaTypeNotSupportedError(Exception):
    postgres_type: str
    column_name: str


def get_pg_response_schema_from_prepared_statement(
    prepared_stmt: asyncpg.prepared_stmt.PreparedStatement,
    python_type_by_postgres_type: dict[str, type[object]],
) -> PgResponseSchema:
    pg_response_schema = {}
    for attribute in prepared_stmt.get_attributes():
        try:
            python_type = python_type_by_postgres_type[attribute.type.name]
        except KeyError:
            raise PgResponseSchemaTypeNotSupportedError(
                postgres_type=attribute.type.name,
                column_name=attribute.name,
            )
        pg_response_schema[attribute.name] = ColumnType(
            type_=python_type, is_optional=True
        )
    return pg_response_schema
