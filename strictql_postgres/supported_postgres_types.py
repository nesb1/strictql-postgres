import enum

from strictql_postgres.python_types import SimpleTypes


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
