import enum

from strictql_postgres.python_types import (
    Bool,
    Bytes,
    DateTimeType,
    DateType,
    DecimalType,
    Float,
    Integer,
    Json,
    SimpleTypes,
    String,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
)


class SupportedPostgresSimpleTypes(enum.Enum):
    SMALLINT = "smallint"
    INTEGER = "integer"
    BIGINT = "bigint"
    REAL = "real"
    DOUBLE_PRECISION = "double precision"
    VARCHAR = "varchar"
    CHAR = "char"
    BPCHAR = "bpchar"
    TEXT = "text"
    BOOL = "bool"
    BYTEA = "bytea"
    JSONB = "jsonb"
    JSON = "json"


class SupportedPostgresTypeRequiredImports(enum.Enum):
    DECIMAL = "decimal"
    NUMERIC = "numeric"
    DATE = "date"
    TIME = "time"
    TIMETZ = "timetz"
    TIMESTAMPTZ = "timestamptz"
    TIMESTAMP = "timestamp"
    INTERVAL = "interval"


PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES: dict[str, type[SimpleTypes]] = {
    "int2": Integer,
    "int4": Integer,
    "int8": Integer,
    "float4": Float,
    "float8": Float,
    "varchar": String,
    "char": String,
    "bpchar": String,
    "text": String,
    "bool": Bool,
    "bytea": Bytes,
    "jsonb": Json,
    "json": Json,
}

PYTHON_TYPE_BY_POSTGRES_TYPE_WHEN_TYPE_REQUIRE_IMPORT: dict[
    str, type[TypesWithImport]
] = {
    "decimal": DecimalType,
    "numeric": DecimalType,
    "date": DateType,
    "time": TimeType,
    "timetz": TimeType,
    "interval": TimeDeltaType,
    "timestamp": DateTimeType,
    "timestamptz": DateTimeType,
}


ALL_SUPPORTED_POSTGRES_TYPES: set[
    SupportedPostgresSimpleTypes | SupportedPostgresTypeRequiredImports
] = {simple_type for simple_type in SupportedPostgresSimpleTypes} | {
    type_required_import
    for type_required_import in SupportedPostgresTypeRequiredImports
}
