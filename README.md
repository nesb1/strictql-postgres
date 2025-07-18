<img src="strictql.png" alt="drawing" width="512"/>

# StrictQL

A utility for generating code to execute raw SQL queries in PostgreSQL.

`pip install strictql-postgres`

## Motivation

The project aims to simplify working with raw queries while keeping them straightforward.

It provides:

- Code generator for executing queries using [asyncpg](https://github.com/MagicStack/asyncpg).
- `pydantic` model generator for database responses.
- Syntax correctness check of the query without executing it.
- Validation of queries against a database without executing it. It verifies that tables and other objects used
  in the query actually exist in the database.
- Work with multiple databases simultaneously, for example, when transferring data from one database to another.
- Ability to integrate checks into CI.

Queries and their parameters are specified in configuration files.

Thus, `StrictQL` solves the following problems:

- Discrepancy between the expected data schema and the actual one in the database.
- Presence of non-working SQL queries in the code.
- Significant time costs for writing, and especially for maintaining queries

## Project status

The project is actively developing, currently only a part of the types is supported. The supported types can be
found [here](https://github.com/nesb1/strictql-postgres/blob/main/strictql_postgres/supported_postgres_types.py)

The remaining types will be added over time.

## Usage Example

- Add these lines to `pyproject.toml`:

```toml
[tool.strictql_postgres]
code_generate_dir = "your_project_name/strictql_generated"
query_files_path = [
    "strictql.toml"
]
[tool.strictql_postgres.databases]
db = { env_name_to_read_connection_url = "DB_URL" }

```

- Create a file with queries `strictql.toml`:

```toml
[queries.select_1]
query = "select 1 as value"
database = "db"
query_type = "fetch"
relative_path = "example.py"
```

- Generate code using the command:

`DB_URL=postgresql://postgres:password@localhost/postgres strictql-postgres generate`

where the environment variable `DB_URL` contains the connection link to your running database.

- The generated code will appear in the directory `your_project_name/strictql_generated`.

- The following code is generated for the query from the example:

```python
from collections.abc import Sequence
from datetime import timedelta

from pydantic import BaseModel

from asyncpg import Connection
from strictql_postgres.api import convert_records_to_pydantic_models


class Select1Model(BaseModel):  # type: ignore[explicit-any]
    value: int | None


async def select_1(
        connection: Connection, timeout: timedelta | None = None
) -> Sequence[Select1Model]:
    query = """
    SELECT 1 AS value
"""
    records = await connection.fetch(
        query, timeout=timeout.total_seconds() if timeout is not None else None
    )
    return convert_records_to_pydantic_models(
        records=records, pydantic_model_type=Select1Model
    )

```

## Supported data types

| Postgres type | Python Type          |
|---------------|----------------------|
| `int2`        | `int`                |
| `int4`        | `int`                |
| `int8`        | `int`                |
| `float4`      | `float`              |
| `float8`      | `float`              |
| `varchar`     | `str`                |
| `char`        | `str`                |
| `bpchar`      | `str`                |
| `text`        | `str`                |
| `bool`        | `bool`               |
| `bytea`       | `bytes`              |
| `decimal`     | `decimal.Decimal`    |
| `numeric`     | `decimal.Decimal`    |
| `date`        | `datetime.date`      |
| `time`        | `datetime.time`      |
| `timetz`      | `datetime.time`      |
| `interval`    | `datetime.timedelta` |
| `timestamp`   | `datetime.datetime`  |
| `timestamptz` | `datetime.datetime`  |
| `jsonb`       | `str`                |
| `json`        | `str`                |

### Arrays

An array option is also available for all supported data types.

However, postgres does not provide information about the dimension of the array at the stage of query preparation, since
this information is dynamic.
Therefore, the type in python looks like a large union in order to protect against errors.

For example, postgres type `integer[]` maps to python type:

```value: list[int | None | list[int | None | list[int | None | object]]] | None```

## Available Commands

- `generate` Generates code based on configuration files
- `check` Checks that the generated code is up to date, convenient to use in `CI`

## Configuration

General `strictql` settings should be in the `pyproject.toml` file

### Specification of pyproject.toml settings

- Settings must be in the `[tool.strictql_postgres]` section.
- `code_generate_dir` - Path to the directory where the code is needed to be generated.
- `query_files_path` - List of files with queries.
- The `tool.strictql_postgres.databases` section must contain database settings.
- Each database must specify the name of the environment variable with the connection string through
  `env_name_to_read_connection_url`. For example: ```db = { env_name_to_read_connection_url = "DB_URL" }```

### Query-file specification

This file contains queries that are needed to be generated.

Each query must start with the section: ```[queries.query_name]```, where `query_name` is the name of the query in
lower snake case format.
Currently, the function name in the generated code has the name `query_name`.
Query fields:

- `query` - SQL query.
- `database` - Name of the database from `pyproject.toml` that this query will be executed against.
- `query_type` - Query type, currently there are three ones: `fetch`, `fetch_row`, and `execute` which correspond to
  methods
  from `asyncpg`.
- `relative_path` - Path to the Python file relative to `code_generate_dir` where the code will be saved. You can
  specify nested directories, `strictql` will create them.

If your query has bind parameters, you need to specify information about them in the section:
`[queries.query_name.parameter_names.parameter_name]`, where `parameter_name` is the name of the parameter in the
generated Python function.
The parameters will correspond to the bind parameter in the query by order.

Parameter fields:

- `is_optional` - Whether the parameter is optional or not.

Example of a query-file:

```toml
[queries.select]
query = "select $1::integer, $2::varchar"
database = "db"
query_type = "fetch_row"
relative_path = "examples/example.py"

[queries.select.parameter_names.first_arg]
is_optional = false

[queries.select.parameter_names.second_arg]
is_optional = false
```

## How Checking Works

It may seem that all these query checks without actually executing them are very difficult to implement, but this is not
the case.

PostgreSQL's binary protocol is used to check queries, it allows preparing a query for execution but not executing
it.
You can read more about the `describe`
command [here](https://www.postgresql.org/docs/current/protocol-message-formats.html).

`StrictQL` is based on [asyncpg](https://github.com/MagicStack/asyncpg), which already provides
the [prepare](https://magicstack.github.io/asyncpg/current/api/index.html#prepared-statements) method.

So `StrictQL` doesn't do anything overly complex with your precious queries, no database will be harmed :)

## Optionality

### <a name="response-model-optional"></a> Response model optionality

If you have already generated code through `strictql`, you might have noticed that all fields in the output models are
optional, even if your table has not `null`-fields.

Unfortunately, this is a problem that currently cannot be solved, as `postgres` does not provide information about
whether a field in the response or query is `NOT NULL` or not.
`postgres` views optionality not as a data type, but
as [constraints](https://www.postgresql.org/docs/current/ddl-constraints.html).

You might object and say that you it can simply get the table name from the query and find out from `postgres` through
the
`pg_attributes` table about the optionality of columns.

Unfortunately, this solution was rejected for the following reasons:

- It requires parsing the SQL query, which `strictql` currently does not do.
- Queries can be quite complex, for example, having a `left join` that will set a `null` value in a `not null` field
  from the right table if it somehow did not join with the left table.

Me personally dislike this limitation for real, however, it's not possible to solve this problem well. The alternative
way is to parse the
query and extract various information from `postgres` - the prototype of it was developed but then deleted because
it turned out to be incredibly complex and unreliable.

### Parameter optionality

I will pay special attention to the query parameters and their optionality through the `is_optional` field.

It is necessary to specify parameter optionality as there are different scenarios for executing queries:

#### Where clause

Imagine we have a query:

`select * table_name where a = $1`

If we execute the query like this:

`select * table_name where a = NULL`

it will always return 0 rows, even if there are `a` values with `NULL` in the table.

[More about this](https://www.postgresql.org/docs/current/functions-comparison.html)

In this case, to avoid mistakes, you need to specify `is_optional=False`

#### Insert

When inserting data into a table, we may need to insert `null` values.

In this case, you need to specify `is_optional=True` in the parameter settings, but keep in mind that if the column has
a `NOT NULL` constraint, inserting a `NULL` value will result in an error. `strictql` cannot check this for reasons
described [above](#response-model-optional)

#### Function call

When calling a function, we may need to pass `NULL` as one of the arguments. In this case, you need to specify
`is_optional=True` in the parameter settings
