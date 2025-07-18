import dataclasses
import itertools
import typing

import pytest

from strictql_postgres.python_types import (
    Bool,
    Bytes,
    DateTimeType,
    DateType,
    DecimalType,
    Float,
    FormattedType,
    GeneratedCodeWithModelDefinitions,
    InnerModelType,
    Integer,
    Json,
    ModelType,
    RecursiveListSupportedTypes,
    RecursiveListType,
    SimpleTypes,
    String,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
    format_simple_type,
    format_type,
    format_type_with_import,
    generate_code_for_model_as_pydantic,
    generate_recursive_list_definition,
)

NAME_BY_SIMPLE_TYPE: dict[type[SimpleTypes], str] = {
    Bool: "bool",
    String: "str",
    Integer: "int",
    Float: "float",
    Bytes: "bytes",
    Json: "str",
}

OPTIONAL_NAME_BY_SIMPLE_TYPE: dict[type[SimpleTypes], str] = {
    type_: name if name == "object" else f"{name} | None"
    for type_, name in NAME_BY_SIMPLE_TYPE.items()
}


@pytest.mark.parametrize(
    ("type_", "expected_str"),
    [
        *[  # type: ignore[misc]
            (
                simple_type(is_optional=False),  # type: ignore[misc]
                NAME_BY_SIMPLE_TYPE[simple_type],  # type: ignore[misc]
            )
            for simple_type in typing.get_args(SimpleTypes)  # type: ignore[misc]
        ],
        *[  # type: ignore[misc]
            (
                simple_type(is_optional=True),  # type: ignore[misc]
                OPTIONAL_NAME_BY_SIMPLE_TYPE[simple_type],  # type: ignore[misc]
            )
            for simple_type in typing.get_args(SimpleTypes)  # type: ignore[misc]
        ],
    ],
)
def test_format_simple_types(type_: SimpleTypes, expected_str: str) -> None:
    assert format_simple_type(type_=type_) == expected_str


@dataclasses.dataclass(frozen=True)
class TestDataForTypesWithImport:
    import_: str
    formatted_type: str


TEST_DATA_FOR_TYPES_WITH_IMPORT: dict[
    type[TypesWithImport], dict[bool, TestDataForTypesWithImport]
] = {
    DecimalType: {
        True: TestDataForTypesWithImport(
            import_="from decimal import Decimal",
            formatted_type="Decimal | None",
        ),
        False: TestDataForTypesWithImport("from decimal import Decimal", "Decimal"),
    },
    DateType: {
        True: TestDataForTypesWithImport("from datetime import date", "date | None"),
        False: TestDataForTypesWithImport("from datetime import date", "date"),
    },
    DateTimeType: {
        True: TestDataForTypesWithImport(
            "from datetime import datetime",
            "datetime | None",
        ),
        False: TestDataForTypesWithImport("from datetime import datetime", "datetime"),
    },
    TimeType: {
        True: TestDataForTypesWithImport("from datetime import time", "time | None"),
        False: TestDataForTypesWithImport("from datetime import time", "time"),
    },
    TimeDeltaType: {
        True: TestDataForTypesWithImport(
            "from datetime import timedelta",
            "timedelta | None",
        ),
        False: TestDataForTypesWithImport(
            "from datetime import timedelta",
            "timedelta",
        ),
    },
}


@pytest.mark.parametrize(
    ("type_with_import", "expected_import", "expected_type"),
    [  # type: ignore[misc]
        (  # type: ignore[misc]
            data_type(is_optional),  # type: ignore[misc]
            test_data.import_,
            test_data.formatted_type,
        )
        for data_type in typing.get_args(TypesWithImport)  # type: ignore[misc]
        for is_optional, test_data in TEST_DATA_FOR_TYPES_WITH_IMPORT[data_type].items()  # type: ignore[misc]
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
            "field": String(is_optional=True),
            "with_import": DateType(
                is_optional=True,
            ),
            "recursive_list": RecursiveListType(
                generic_type=Bool(is_optional=True),
                is_optional=True,
            ),
        },
    )
    res = generate_code_for_model_as_pydantic(
        model_type=ModelType(
            name="TestModel",
            fields={
                "text_field": String(is_optional=True),
                "with_import": TimeType(
                    is_optional=True,
                ),
                "recursive_list": RecursiveListType(
                    generic_type=Integer(is_optional=True),
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
    with_import: date | None
    recursive_list: list[bool | None | list[bool | None | list[bool | None | object]]] | None"""
    test_model_code = """
class TestModel(BaseModel): # type: ignore[explicit-any]
    text_field: str | None
    with_import: time | None
    recursive_list: list[int | None | list[int | None | list[int | None | object]]] | None
    inner_optional: InnerModel | None
    inner: InnerModel"""

    assert (
        GeneratedCodeWithModelDefinitions(
            imports={
                "from pydantic import BaseModel",
                "from datetime import time",
                "from datetime import date",
                "from typing import Union",
                "from typing import TypeAliasType",
            },
            main_model_name="TestModel",
            models_code={inner_model_code.strip(), test_model_code.strip()},
        )
        == res
    )


RECURSIVE_LIST_TYPE_IMPORTS = {
    "from typing import Union",
    "from typing import TypeAliasType",
}


@dataclasses.dataclass(frozen=True)
class TestDataForRecursiveList:
    type_: RecursiveListSupportedTypes
    expected_type: str
    is_optional: bool


TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR: dict[
    type[RecursiveListSupportedTypes],
    list[TestDataForRecursiveList],
] = {}

simple_type: type[SimpleTypes]
for simple_type in typing.get_args(SimpleTypes):  # type: ignore[misc]
    cases = []
    for is_optional_type, is_optional_recursive_list in itertools.product(
        [True, False], [True, False]
    ):
        instance_of_simple_type = simple_type(is_optional=is_optional_type)
        formatted_simple_type = format_simple_type(type_=instance_of_simple_type)
        list_type_postfix = " | None" if is_optional_recursive_list else ""
        cases.append(
            TestDataForRecursiveList(
                type_=instance_of_simple_type,
                expected_type=f"list[{formatted_simple_type} | list[{formatted_simple_type} | list[{formatted_simple_type} | object]]]{list_type_postfix}",
                is_optional=is_optional_recursive_list,
            )
        )
    TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR[simple_type] = cases

type_with_import: type[TypesWithImport]
for type_with_import in typing.get_args(TypesWithImport):  # type: ignore[misc]
    cases = []
    for is_optional_type, is_optional_recursive_list in itertools.product(
        [True, False], [True, False]
    ):
        type_with_import_instance = type_with_import(is_optional=is_optional_type)
        formatted_type_with_import = format_type_with_import(
            type_=type_with_import_instance,
        ).type_as_str
        list_type_postfix = " | None" if is_optional_recursive_list else ""
        cases.append(
            TestDataForRecursiveList(
                type_=type_with_import_instance,
                expected_type=f"list[{formatted_type_with_import} | list[{formatted_type_with_import} | list[{formatted_type_with_import} | object]]]{list_type_postfix}",
                is_optional=is_optional_recursive_list,
            )
        )
    TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR[type_with_import] = cases


@pytest.mark.parametrize(
    ("inner_type", "expected_formatted_type", "is_optional"),
    [
        (
            case.type_,
            case.expected_type,
            case.is_optional,
        )
        for data_type, cases in TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR.items()
        for case in cases
    ],
)
def test_generate_code_for_recursive_list(
    inner_type: RecursiveListSupportedTypes,
    expected_formatted_type: str,
    is_optional: bool,
) -> None:
    formatted_inner_type = format_type(inner_type)

    expected_type = FormattedType(
        imports=formatted_inner_type.imports | RECURSIVE_LIST_TYPE_IMPORTS,
        models_code=set(),
        type_=expected_formatted_type,
    )
    actual = generate_recursive_list_definition(
        t=RecursiveListType(generic_type=inner_type, is_optional=is_optional)
    )

    assert actual == expected_type
