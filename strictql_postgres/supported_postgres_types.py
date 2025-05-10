import enum

from strictql_postgres.python_types import (
    DateTimeType,
    DateType,
    DecimalType,
    SimpleTypes,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
)


class SupportedPostgresSimpleTypes(enum.Enum):
    SMALLINT = "smallint"
    INTEGER = "integer"
    BIGINT = "bigint"
    REAL = "real"
    DOUBLE_PRECISION = "double_precision"
    VARCHAR = "varchar"
    CHAR = "char"
    BPCHAR = "bpchar"
    TEXT = "text"


class SupportedPostgresTypeRequiredImports(enum.Enum):
    DECIMAL = "decimal"
    NUMERIC = "numeric"
    DATE = "date"
    TIME = "time"
    TIMETZ = "timetz"
    TIMESTAMPTZ = "timestamptz"
    TIMESTAMP = "timestamp"
    INTERVAL = "interval"


PYTHON_TYPE_BY_POSTGRES_SIMPLE_TYPES = {
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
