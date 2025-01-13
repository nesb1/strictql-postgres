import enum


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
