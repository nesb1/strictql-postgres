import pytest

from strictql_postgres.type_str_creator import create_type_str


@pytest.mark.parametrize(
    ("type_", "is_optional", "expected_type_str"),
    [
        ("str", True, "str | None"),
        ("str", False, "str"),
    ],
)
def test_create_type_str(type_: str, is_optional: bool, expected_type_str: str) -> None:
    assert create_type_str(type_, is_optional) == expected_type_str
