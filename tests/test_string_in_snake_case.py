import pytest

from strictql_postgres.string_in_snake_case import (
    StringInSnakeLowerCase,
    StringNotInLowerSnakeCase,
)


@pytest.mark.parametrize(
    "value",
    [
        "a",
        "a_c",
        "a_c_asdasd_a",
    ],
)
def test_string_in_snake_case_valid(value: str) -> None:
    StringInSnakeLowerCase(value=value)


@pytest.mark.parametrize(
    "value",
    [
        "A",
        "a_A",
        "BBasda",
        "CamelCase",
        "lowerCamelCase",
    ],
)
def test_string_in_snake_case_not_valid(value: str) -> None:
    with pytest.raises(StringNotInLowerSnakeCase):
        StringInSnakeLowerCase(value=value)
