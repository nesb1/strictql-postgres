import pytest

from strictql_postgres.model_name_generator import (
    generate_model_name_by_function_name,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase


@pytest.mark.parametrize(
    ("function_name", "expected_model_name"),
    [
        (StringInSnakeLowerCase("get_users"), "GetUsersModel"),
        (StringInSnakeLowerCase("withoutunderscore"), "WithoutunderscoreModel"),
    ],
)
def test_generate_model_name_by_function_name(
    function_name: StringInSnakeLowerCase, expected_model_name: str
) -> None:
    assert (
        generate_model_name_by_function_name(function_name=function_name)
        == expected_model_name
    )
