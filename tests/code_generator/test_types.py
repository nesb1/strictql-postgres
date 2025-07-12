import dataclasses
import typing

import pytest

from strictql_postgres.python_types import (
    DateTimeType,
    DateType,
    DecimalType,
    FormattedType,
    GeneratedCodeWithModelDefinitions,
    InnerModelType,
    ModelType,
    RecursiveListSupportedTypes,
    RecursiveListType,
    SimpleType,
    SimpleTypes,
    TimeDeltaType,
    TimeType,
    TypesWithImport,
    format_simple_type,
    format_type_with_import,
    generate_code_for_model_as_pydantic,
    generate_recursive_list_definition,
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
            "field": SimpleType(type_=SimpleTypes.STR, is_optional=True),
            "with_import": DateType(
                is_optional=True,
            ),
            "recursive_list": RecursiveListType(
                generic_type=SimpleType(type_=SimpleTypes.BOOL, is_optional=True),
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
                "recursive_list": RecursiveListType(
                    generic_type=SimpleType(type_=SimpleTypes.INT, is_optional=True),
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
    recursive_list: OptionalRecursiveListOfOptionalBool"""
    test_model_code = """
class TestModel(BaseModel): # type: ignore[explicit-any]
    text_field: str | None
    with_import: time | None
    recursive_list: OptionalRecursiveListOfOptionalInt
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
            type_definitions={
                'OptionalRecursiveListOfOptionalInt = TypeAliasType("OptionalRecursiveListOfOptionalInt", Union[list[int | None], list["OptionalRecursiveListOfOptionalInt"], None])'
            },
        )
        == res
    )


RECURSIVE_LIST_TYPE_IMPORTS = {
    "from typing import Union",
    "from typing import TypeAliasType",
}
RECURSIVE_LIST_TYPE_MODELS_CODE: set[str] = set()


@dataclasses.dataclass(frozen=True)
class TestDataForRecursiveList:
    type_: RecursiveListSupportedTypes
    expected_formatted_type: FormattedType
    is_optional: bool


TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR: dict[
    type[RecursiveListSupportedTypes],
    list[TestDataForRecursiveList],
] = {
    SimpleType: [
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.STR, is_optional=True),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="OptionalRecursiveListOfOptionalStr",
                type_definitions={
                    'OptionalRecursiveListOfOptionalStr = TypeAliasType("OptionalRecursiveListOfOptionalStr", Union[list[str | None], list["OptionalRecursiveListOfOptionalStr"], None])'
                },
            ),
            is_optional=True,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.STR, is_optional=False),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="OptionalRecursiveListOfStr",
                type_definitions={
                    'OptionalRecursiveListOfStr = TypeAliasType("OptionalRecursiveListOfStr", Union[list[str], list["OptionalRecursiveListOfStr"], None])'
                },
            ),
            is_optional=True,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.STR, is_optional=True),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="RecursiveListOfOptionalStr",
                type_definitions={
                    'RecursiveListOfOptionalStr = TypeAliasType("RecursiveListOfOptionalStr", Union[list[str | None], list["RecursiveListOfOptionalStr"]])'
                },
            ),
            is_optional=False,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.STR, is_optional=False),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="RecursiveListOfStr",
                type_definitions={
                    'RecursiveListOfStr = TypeAliasType("RecursiveListOfStr", Union[list[str], list["RecursiveListOfStr"]])'
                },
            ),
            is_optional=False,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.INT, is_optional=True),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="OptionalRecursiveListOfOptionalInt",
                type_definitions={
                    'OptionalRecursiveListOfOptionalInt = TypeAliasType("OptionalRecursiveListOfOptionalInt", Union[list[int | None], list["OptionalRecursiveListOfOptionalInt"], None])'
                },
            ),
            is_optional=True,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.INT, is_optional=False),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="OptionalRecursiveListOfInt",
                type_definitions={
                    'OptionalRecursiveListOfInt = TypeAliasType("OptionalRecursiveListOfInt", Union[list[int], list["OptionalRecursiveListOfInt"], None])'
                },
            ),
            is_optional=True,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.INT, is_optional=True),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="RecursiveListOfOptionalInt",
                type_definitions={
                    'RecursiveListOfOptionalInt = TypeAliasType("RecursiveListOfOptionalInt", Union[list[int | None], list["RecursiveListOfOptionalInt"]])'
                },
            ),
            is_optional=False,
        ),
        TestDataForRecursiveList(
            type_=SimpleType(type_=SimpleTypes.INT, is_optional=False),
            expected_formatted_type=FormattedType(
                imports=RECURSIVE_LIST_TYPE_IMPORTS,
                models_code=RECURSIVE_LIST_TYPE_MODELS_CODE,
                type_="RecursiveListOfInt",
                type_definitions={
                    'RecursiveListOfInt = TypeAliasType("RecursiveListOfInt", Union[list[int], list["RecursiveListOfInt"]])'
                },
            ),
            is_optional=False,
        ),
    ]
}


def test_data_for_recursive_list_fullness() -> None:
    data_type: type[RecursiveListSupportedTypes]
    for data_type in typing.get_args(RecursiveListSupportedTypes):  # type: ignore[misc]
        if issubclass(data_type, SimpleType):
            if data_type not in TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR:
                pytest.fail(f"Type: {data_type} not exists in test data")
            simple_type_cases = TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR[
                data_type
            ]
            assert len(simple_type_cases) > 0
            for simple_type in SimpleTypes:
                found_type = False
                found_all_optional_combinations = {
                    True: {
                        True: False,
                        False: False,
                    },
                    False: {
                        True: False,
                        False: False,
                    },
                }

                for case in simple_type_cases:
                    if not isinstance(case.type_, SimpleType):
                        pytest.fail("Invalid type: {case.type_} in simple types cases")
                    if case.type_.type_ == simple_type:
                        found_type = True
                        found_all_optional_combinations[case.is_optional][
                            case.type_.is_optional
                        ] = True
                assert found_type
                assert found_all_optional_combinations == {
                    True: {
                        True: True,
                        False: True,
                    },
                    False: {
                        True: True,
                        False: True,
                    },
                }

        if issubclass(data_type, TypesWithImport):
            if data_type not in TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR:
                pytest.fail(f"Type: {data_type} not exists in test data")
            cases = TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR[data_type]
            assert len(cases) > 0
            found_type = False
            found_all_optional_combinations = {
                True: {
                    True: False,
                    False: False,
                },
                False: {
                    True: False,
                    False: False,
                },
            }
            type_with_import: type[TypesWithImport]
            for type_with_import in typing.get_args(TypesWithImport):  # type: ignore[misc]
                for case in cases:
                    if isinstance(case.type_, type_with_import):
                        found_type = True
                        found_all_optional_combinations[case.is_optional][
                            case.type_.is_optional
                        ] = True
            assert found_type
            assert found_all_optional_combinations == {
                True: {
                    True: True,
                    False: True,
                },
                False: {
                    True: True,
                    False: True,
                },
            }

        pytest.fail(f"Type: {data_type} not supported yet")


@pytest.mark.parametrize(
    ("inner_type", "expected_formatted_type", "is_optional"),
    [
        (
            case.type_,
            case.expected_formatted_type,
            case.is_optional,
        )
        for data_type, cases in TEST_DATA_FOR_TEST_RECURSIVE_LIST_CODE_GENERATOR.items()
        for case in cases
    ],
)
def test_generate_code_for_recursive_list(
    inner_type: RecursiveListSupportedTypes,
    expected_formatted_type: FormattedType,
    is_optional: bool,
) -> None:
    actual = generate_recursive_list_definition(
        t=RecursiveListType(generic_type=inner_type, is_optional=is_optional)
    )

    assert actual == expected_formatted_type
