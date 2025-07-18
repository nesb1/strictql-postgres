import dataclasses
import datetime
import decimal
from typing import Sequence

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
from strictql_postgres.supported_postgres_types import (
    SupportedPostgresSimpleTypes,
    SupportedPostgresTypeRequiredImports,
)


@dataclasses.dataclass
class TypeTestData:
    cast_str: str
    postgres_value_as_str: str
    expected_python_value: object
    expected_python_type: type[object]


@dataclasses.dataclass()
class SimpleTypeTestData:
    test_data: TypeTestData
    simple_type: type[SimpleTypes]


@dataclasses.dataclass()
class TypeWithImportTestData:
    test_data: TypeTestData
    type_with_import: type[TypesWithImport]


TEST_DATA_FOR_SIMPLE_TYPES: dict[
    SupportedPostgresSimpleTypes, list[SimpleTypeTestData]
] = {
    SupportedPostgresSimpleTypes.SMALLINT: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="smallint",
                postgres_value_as_str="1",
                expected_python_value=1,
                expected_python_type=int,
            ),
            simple_type=Integer,
        )
    ],
    SupportedPostgresSimpleTypes.INTEGER: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="integer",
                postgres_value_as_str="1",
                expected_python_value=1,
                expected_python_type=int,
            ),
            simple_type=Integer,
        )
    ],
    SupportedPostgresSimpleTypes.BIGINT: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="bigint",
                postgres_value_as_str="1",
                expected_python_value=1,
                expected_python_type=int,
            ),
            simple_type=Integer,
        )
    ],
    SupportedPostgresSimpleTypes.REAL: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="real",
                postgres_value_as_str="123.1",
                expected_python_type=float,
                expected_python_value=123.1,
            ),
            simple_type=Float,
        )
    ],
    SupportedPostgresSimpleTypes.DOUBLE_PRECISION: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="double precision",
                postgres_value_as_str="123.1",
                expected_python_value=123.1,
                expected_python_type=float,
            ),
            simple_type=Float,
        )
    ],
    SupportedPostgresSimpleTypes.VARCHAR: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="varchar",
                postgres_value_as_str="'kek'",
                expected_python_value="kek",
                expected_python_type=str,
            ),
            simple_type=String,
        )
    ],
    SupportedPostgresSimpleTypes.CHAR: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="char(1)",
                postgres_value_as_str="'k'",
                expected_python_value="k",
                expected_python_type=str,
            ),
            simple_type=String,
        )
    ],
    SupportedPostgresSimpleTypes.BPCHAR: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="bpchar(1)",
                postgres_value_as_str="'k'",
                expected_python_value="k",
                expected_python_type=str,
            ),
            simple_type=String,
        )
    ],
    SupportedPostgresSimpleTypes.TEXT: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="text",
                postgres_value_as_str="'kek'",
                expected_python_value="kek",
                expected_python_type=str,
            ),
            simple_type=String,
        )
    ],
    SupportedPostgresSimpleTypes.BOOL: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="bool",
                postgres_value_as_str="'true'",
                expected_python_value=True,
                expected_python_type=bool,
            ),
            simple_type=Bool,
        )
    ],
    SupportedPostgresSimpleTypes.BYTEA: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="bytea",
                postgres_value_as_str="'kek'",
                expected_python_value="kek".encode("utf-8"),
                expected_python_type=bytes,
            ),
            simple_type=Bytes,
        )
    ],
    SupportedPostgresSimpleTypes.JSONB: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="jsonb",
                postgres_value_as_str='\'{"key":"value"}\'',
                expected_python_value='{"key": "value"}',
                expected_python_type=str,
            ),
            simple_type=Json,
        )
    ],
    SupportedPostgresSimpleTypes.JSON: [
        SimpleTypeTestData(
            test_data=TypeTestData(
                cast_str="json",
                postgres_value_as_str='\'{"key":"value"}\'',
                expected_python_value='{"key":"value"}',
                expected_python_type=str,
            ),
            simple_type=Json,
        )
    ],
}


TEST_DATA_FOR_TYPES_WITH_IMPORT: dict[
    SupportedPostgresTypeRequiredImports, list[TypeWithImportTestData]
] = {
    SupportedPostgresTypeRequiredImports.NUMERIC: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="numeric",
                postgres_value_as_str="'1.012'",
                expected_python_value=decimal.Decimal("1.012"),
                expected_python_type=decimal.Decimal,
            ),
            type_with_import=DecimalType,
        )
    ],
    SupportedPostgresTypeRequiredImports.DECIMAL: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="decimal",
                postgres_value_as_str="'1.012'",
                expected_python_value=decimal.Decimal("1.012"),
                expected_python_type=decimal.Decimal,
            ),
            type_with_import=DecimalType,
        )
    ],
    SupportedPostgresTypeRequiredImports.DATE: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="date",
                postgres_value_as_str="'2020-07-09'",
                expected_python_value=datetime.date(year=2020, month=7, day=9),
                expected_python_type=datetime.date,
            ),
            type_with_import=DateType,
        )
    ],
    SupportedPostgresTypeRequiredImports.TIME: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="time without time zone",
                postgres_value_as_str="'09:08:00'",
                expected_python_value=datetime.time(hour=9, minute=8, second=0),
                expected_python_type=datetime.time,
            ),
            type_with_import=TimeType,
        )
    ],
    SupportedPostgresTypeRequiredImports.TIMETZ: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="time with time zone",
                postgres_value_as_str="'09:08:00'",
                expected_python_value=datetime.time(
                    hour=9, minute=8, second=0, tzinfo=datetime.timezone.utc
                ),
                expected_python_type=datetime.time,
            ),
            type_with_import=TimeType,
        )
    ],
    SupportedPostgresTypeRequiredImports.TIMESTAMPTZ: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="timestamp with time zone",
                postgres_value_as_str="'2020-07-09T09:08:00'",
                expected_python_value=datetime.datetime(
                    year=2020,
                    month=7,
                    day=9,
                    hour=9,
                    minute=8,
                    second=0,
                    tzinfo=datetime.timezone.utc,
                ),
                expected_python_type=datetime.datetime,
            ),
            type_with_import=DateTimeType,
        )
    ],
    SupportedPostgresTypeRequiredImports.TIMESTAMP: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="timestamp without time zone",
                postgres_value_as_str="'2020-07-09T09:08:00'",
                expected_python_value=datetime.datetime(
                    year=2020,
                    month=7,
                    day=9,
                    hour=9,
                    minute=8,
                    second=0,
                ),
                expected_python_type=datetime.datetime,
            ),
            type_with_import=DateTimeType,
        )
    ],
    SupportedPostgresTypeRequiredImports.INTERVAL: [
        TypeWithImportTestData(
            test_data=TypeTestData(
                cast_str="interval",
                postgres_value_as_str="'1 year'",
                expected_python_value=datetime.timedelta(days=365),
                expected_python_type=datetime.timedelta,
            ),
            type_with_import=TimeDeltaType,
        )
    ],
}

TEST_DATA_FOR_ALL_TYPES: dict[
    SupportedPostgresTypeRequiredImports | SupportedPostgresSimpleTypes,
    Sequence[SimpleTypeTestData | TypeWithImportTestData],
] = {}

for data_type, simple_type_test_data in TEST_DATA_FOR_SIMPLE_TYPES.items():
    TEST_DATA_FOR_ALL_TYPES[data_type] = simple_type_test_data

for data_type_with_import, test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT.items():
    TEST_DATA_FOR_ALL_TYPES[data_type_with_import] = test_data
