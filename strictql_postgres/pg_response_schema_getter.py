import dataclasses
import keyword
import re
from typing import Mapping

import asyncpg.prepared_stmt
from strictql_postgres.common_types import ColumnType
from strictql_postgres.python_types import (
    ALL_TYPES,
    RecursiveListType,
)
from strictql_postgres.supported_postgres_types import (
    PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES,
    PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT,
)

PgResponseSchema = dict[str, ColumnType]


@dataclasses.dataclass
class PgResponseSchemaContainsColumnsWithInvalidNames:
    column_names: list[str]
    invalid_column_names: list[str]

    def __str__(self) -> str:
        return f"column_names: {self.column_names}, invalid_column_names: {self.invalid_column_names}"


@dataclasses.dataclass
class PgResponseSchemaContainsColumnsWithNotUniqueNames:
    column_names: list[str]
    not_unique_column_names: set[str]

    def __str__(self) -> str:
        return f"column_names: {self.column_names}, not_unique_column_names: {self.not_unique_column_names}"


@dataclasses.dataclass
class PgResponseSchemaTypeNotSupported:
    postgres_type: str
    column_name: str

    def __str__(self) -> str:
        return f"postgres_type: {self.postgres_type} not supported yet, column_name: {self.column_name}"


@dataclasses.dataclass
class PgResponseSchemaGetterError(Exception):
    error: (
        PgResponseSchemaTypeNotSupported
        | PgResponseSchemaContainsColumnsWithInvalidNames
        | PgResponseSchemaContainsColumnsWithNotUniqueNames
    )


def get_pg_response_schema_from_prepared_statement(
    prepared_stmt: asyncpg.prepared_stmt.PreparedStatement,
) -> Mapping[str, ALL_TYPES]:
    invalid_column_names = []
    column_names = []
    unique_column_names = set()
    not_unique_column_names = set()
    for attribute in prepared_stmt.get_attributes():
        column_names.append(attribute.name)
        if attribute.name in unique_column_names:
            not_unique_column_names.add(attribute.name)
        unique_column_names.add(attribute.name)

        if (
            keyword.iskeyword(attribute.name)
            or keyword.issoftkeyword(attribute.name)
            or re.fullmatch("[a-zA-Z_][a-zA-Z_0-9]*", string=attribute.name) is None
        ):
            invalid_column_names.append(attribute.name)
            continue

    if len(invalid_column_names) > 0:
        raise PgResponseSchemaGetterError(
            error=PgResponseSchemaContainsColumnsWithInvalidNames(
                column_names=column_names,
                invalid_column_names=invalid_column_names,
            )
        )
    if len(not_unique_column_names) > 0:
        raise PgResponseSchemaGetterError(
            PgResponseSchemaContainsColumnsWithNotUniqueNames(
                column_names=column_names,
                not_unique_column_names=not_unique_column_names,
            )
        )

    pg_response_schema: dict[str, ALL_TYPES] = {}
    for attribute in prepared_stmt.get_attributes():
        is_array = False
        attribute_type_name = attribute.type.name
        if attribute.type.name.endswith("[]"):
            is_array = True
            attribute_type_name = attribute.type.name.removesuffix("[]")

        python_simple_type = PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES.get(
            attribute_type_name
        )

        if python_simple_type is not None:
            if not is_array:
                pg_response_schema[attribute.name] = python_simple_type(
                    is_optional=True
                )

                continue
            pg_response_schema[attribute.name] = RecursiveListType(
                generic_type=python_simple_type(is_optional=True),
                is_optional=True,
            )

            continue

        type_with_import = PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT.get(
            attribute_type_name
        )

        if type_with_import is not None:
            if not is_array:
                pg_response_schema[attribute.name] = type_with_import(is_optional=True)
                continue
            pg_response_schema[attribute.name] = RecursiveListType(
                generic_type=type_with_import(is_optional=True), is_optional=True
            )
            continue

        raise PgResponseSchemaGetterError(
            PgResponseSchemaTypeNotSupported(
                postgres_type=attribute.type.name,
                column_name=attribute.name,
            )
        )
    return pg_response_schema
