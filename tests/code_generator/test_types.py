import pytest

from strictql_postgres.python_types import (
    DateTimeType,
    DateType,
    DecimalType,
    GeneratedCodeWithModelDefinitions,
    InnerModelType,
    ModelType,
    SimpleType,
    SimpleTypes,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
    format_simple_type,
    format_type_with_import,
    generate_code_for_model_as_pydantic,
)


@pytest.mark.parametrize(
    ("type_", "expected_str"),
    [
        *[
            (
                SimpleType(type_=simple_type, is_optional=False),
                simple_type.value,
            )
            for simple_type in SimpleTypes
        ],
        *[
            (
                SimpleType(type_=simple_type, is_optional=True),
                f"{simple_type.value} | None",
            )
            for simple_type in SimpleTypes
        ],
    ],
)
def test_format_simple_types(type_: SimpleType, expected_str: str) -> None:
    assert format_simple_type(type_=type_) == expected_str


@pytest.mark.parametrize(
    ("type_with_import", "expected_import", "expected_type"),
    [
        (
            DecimalType(is_optional=True),
            "from decimal import Decimal",
            "Decimal | None",
        ),
        (DecimalType(is_optional=False), "from decimal import Decimal", "Decimal"),
        (DateType(is_optional=True), "from datetime import date", "date | None"),
        (DateType(is_optional=False), "from datetime import date", "date"),
        (
            DateTimeType(is_optional=True),
            "from datetime import datetime",
            "datetime | None",
        ),
        (DateTimeType(is_optional=False), "from datetime import datetime", "datetime"),
        (TimeType(is_optional=True), "from datetime import time", "time | None"),
        (TimeType(is_optional=False), "from datetime import time", "time"),
        (
            TimeDeltaType(is_optional=True),
            "from datetime import timedelta",
            "timedelta | None",
        ),
        (
            TimeDeltaType(is_optional=False),
            "from datetime import timedelta",
            "timedelta",
        ),
    ],
)
def test_format_types_with_import(
    type_with_import: TypesWithImport, expected_import: str, expected_type: str
) -> None:
    formatted_type = format_type_with_import(type_=type_with_import)
    assert formatted_type.type_as_str == expected_type
    assert formatted_type.import_as_str == expected_import
    code = f"""
{formatted_type.import_as_str}

{formatted_type.type_as_str}
"""
    exec(code)


def test_format_model_as_pydantic_model() -> None:
    inner_model_type = ModelType(
        name="InnerModel",
        fields={
            "field": SimpleType(type_=SimpleTypes.STR, is_optional=True),
            "with_import": DateType(
                is_optional=True,
            ),
        },
    )
    res = generate_code_for_model_as_pydantic(
        model_type=ModelType(
            name="TestModel",
            fields={
                "text_field": SimpleType(type_=SimpleTypes.STR, is_optional=True),
                "with_import": TimeType(
                    is_optional=True,
                ),
                "inner_optional": InnerModelType(
                    model_type=inner_model_type,
                    is_optional=True,
                ),
                "inner": InnerModelType(
                    model_type=inner_model_type,
                    is_optional=False,
                ),
            },
        )
    )
    inner_model_code = """
class InnerModel(BaseModel): # type: ignore[explicit-any]
    field: str | None
    with_import: date | None"""
    test_model_code = """
class TestModel(BaseModel): # type: ignore[explicit-any]
    text_field: str | None
    with_import: time | None
    inner_optional: InnerModel | None
    inner: InnerModel"""

    assert (
        GeneratedCodeWithModelDefinitions(
            imports={
                "from pydantic import BaseModel",
                "from datetime import time",
                "from datetime import date",
            },
            main_model_name="TestModel",
            models_code={inner_model_code.strip(), test_model_code.strip()},
        )
        == res
    )
