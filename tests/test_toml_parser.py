import pathlib
import tempfile

import pytest

from strictql_postgres.toml_parser import (
    TomlNotFoundError,
    TomlNotValidTomlError,
    parse_toml_file,
)


def test_toml_parser_works() -> None:
    pyproject_content = """
[tool.kek]
param = "1"
params = [
    "value1",
    "value2",
]    
"""
    expected = {
        "tool": {
            "kek": {
                "param": "1",
                "params": [
                    "value1",
                    "value2",
                ],
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode="r+") as tmp_file:
        tmp_file.write(pyproject_content)
        tmp_file.seek(0)
        actual = parse_toml_file(path=pathlib.Path(tmp_file.name))

    assert actual == expected


def test_toml_parser_raises_error_when_file_not_found() -> None:
    path = pathlib.Path("not_existed_pyproject.toml")
    with pytest.raises(TomlNotFoundError) as error:
        parse_toml_file(path=path)
    assert error.value.path


def test_toml_parser_raises_error_when_invalid_toml() -> None:
    pyproject_content = """invalid_toml"""

    with tempfile.NamedTemporaryFile(mode="r+") as tmp_file:
        tmp_file.write(pyproject_content)
        tmp_file.seek(0)

        with pytest.raises(TomlNotValidTomlError) as error:
            parse_toml_file(path=pathlib.Path(tmp_file.name))

        assert (
            error.value.error
            == "Expected '=' after a key in a key/value pair (at end of document)"
        )
