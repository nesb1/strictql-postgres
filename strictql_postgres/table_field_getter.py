import dataclasses

import asyncpg


@dataclasses.dataclass
class TableField:
    num: int
    not_null: bool
    type_id: int


class TableFieldGetterError(Exception):
    pass


@dataclasses.dataclass()
class TableNotExistsError(TableFieldGetterError):
    table_name: str


async def get_table_fields(
    connection: asyncpg.Connection, table_name: str
) -> dict[str, TableField]:
    row = await connection.fetchrow(
        "select oid as table_oid from pg_class where relname = $1", table_name
    )

    if row is None:
        raise TableNotExistsError(table_name=table_name)

    table_oid = row.get("table_oid")

    if not isinstance(table_oid, int):
        raise TableFieldGetterError(
            f"Unexpected table oid type: {type(table_oid)}, value {table_oid}, expected type: str"
        )

    rows = await connection.fetch(
        "select attname, attnum, attnotnull, atttypid from pg_attribute where attrelid = $1 and attnum > 0",
        table_oid,
    )
    fields: dict[str, TableField] = {}
    for row in rows:
        att_num = row.get("attnum")
        not_null = row.get("attnotnull")
        type_id = row.get("atttypid")
        name = row.get("attname")

        if table_oid is None:
            raise TableNotExistsError(table_name)

        if not isinstance(att_num, int):
            raise ValueError(
                f"Column attnum has unexpected type: {type(att_num)}, values: {att_num}"
            )
        if not isinstance(not_null, bool):
            raise ValueError("")
        if not isinstance(type_id, int):
            raise ValueError("")
        if not isinstance(name, str):
            raise ValueError("")

        fields[name] = TableField(
            num=att_num,
            not_null=not_null,
            type_id=type_id,
        )

    return fields
