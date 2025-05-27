import os
import pathlib

import pytest

from strictql_postgres.config_manager import (
    extract_strictql_settings_from_parsed_toml_file,
    ParsedStrictqlSettings,
    ExtractStrictqlSettingsError,
    resolve_strictql_settings_from_parsed_settings,
    parse_query_file_content,
    ParsedQueryToGenerate,
    QueryFileContentParserError,
    create_path_object_from_str,
    PathValidationError,
    ParsedDatabase,
)


def test_extract_strictql_settings_from_parsed_toml_file_works():
    assert extract_strictql_settings_from_parsed_toml_file(
        {
            "tool": {
                "strictql_postgres": {
                    "code_generate_dir": "dir",
                    "query_files_path": [
                        "path1",
                        "path2",
                    ],
                    "databases": {"db1": {"env_name_to_read_connection_url": "KEK"}},
                }
            }
        }
    ) == ParsedStrictqlSettings(
        query_files_path=["path1", "path2"],
        code_generate_dir="dir",
        databases={"db1": ParsedDatabase(env_name_to_read_connection_url="KEK")},
    )


@pytest.mark.parametrize(
    ("pyproject_data", "expected_error"),
    [
        pytest.param(
            {},
            "Missing `tool` section in pyproject.toml",
            id="empty",
        ),
        pytest.param(
            {"tool": {}},
            "Missing `tool.strictql_postgres` section in pyproject.toml",
            id="empty tool",
        ),
        pytest.param(
            {
                "tool": {
                    "strictql_postgres": {
                        "code_generate_dir": "dir",
                    }
                }
            },
            "Missing `tool.strictql_postgres.query_files_path` section in pyproject.toml",
            id="query_files not exists",
        ),
        pytest.param(
            {
                "tool": {
                    "strictql_postgres": {
                        "code_generate_dir": "dir",
                        "query_files_path": "1",
                    }
                }
            },
            "Input should be a valid list for option `tool.strictql_postgres.query_files_path` in pyproject.toml",
            id="query_files invalid type",
        ),
        pytest.param(
            {
                "tool": {
                    "strictql_postgres": {
                        "code_generate_dir": "dir",
                        "query_files_path": [1],
                    }
                }
            },
            "Input should be a valid string for option `tool.strictql_postgres.query_files_path.0` in pyproject.toml",
            id="query_files invalid type list",
        ),
        pytest.param(
            {
                "tool": {
                    "strictql_postgres": {
                        "query_files_path": ["dir"],
                    }
                }
            },
            "Missing `tool.strictql_postgres.code_generate_dir` section in pyproject.toml",
            id="code_generate_dir not exists",
        ),
        pytest.param(
            {
                "tool": {
                    "strictql_postgres": {
                        "query_files_path": ["dir"],
                        "code_generate_dir": 1,
                    }
                }
            },
            "Input should be a valid string for option `tool.strictql_postgres.code_generate_dir` in pyproject.toml",
            id="code_generate_dir invalid type",
        ),
        pytest.param(
            {"tool": []},
            "Error when validating section `tool`, it must be valid toml table`",
            id="invalid tool section type",
        ),
        pytest.param(
            {"tool": {"strictql_postgres": []}},
            "Error when validating section `tool.strictql_postgres`, it must be valid toml table`",
            id="invalid tool section type",
        ),
    ],
)
def test_raises_extract_error(pyproject_data: dict[str, object], expected_error: str):
    with pytest.raises(ExtractStrictqlSettingsError) as error:
        extract_strictql_settings_from_parsed_toml_file(pyproject_data=pyproject_data)

    assert error.value.error == expected_error


def test_parse_query_content_file_works() -> None:
    actual_queries = parse_query_file_content(
        query_file_content={
            "queries": {
                "query_name1": {
                    "query": "select * from table",
                    "parameter_names": {
                        "param1": {
                            "is_optional": True,
                        },
                        "param2": {
                            "is_optional": True,
                        },
                    },
                    "database": "db1",
                    "return_type": "list",
                    "function_name": "my_func",
                },
                "query_name2": {
                    "query": "select * from table",
                    "parameter_names": {
                        "param1": {
                            "is_optional": True,
                        },
                        "param2": {
                            "is_optional": True,
                        },
                    },
                    "database": "db1",
                    "return_type": "list",
                    "function_name": "my_func",
                },
            }
        }
    )

    expected_queries = {
        "query_name1": ParsedQueryToGenerate(
            query="select * from table",
            parameter_names={
                "param1": {
                    "is_optional": True,
                },
                "param2": {
                    "is_optional": True,
                },
            },
            database="db1",
            return_type="list",
            function_name="my_func",
        ),
        "query_name2": ParsedQueryToGenerate(
            query="select * from table",
            parameter_names={
                "param1": {
                    "is_optional": True,
                },
                "param2": {
                    "is_optional": True,
                },
            },
            database="db1",
            return_type="list",
            function_name="my_func",
        ),
    }

    assert actual_queries == expected_queries


@pytest.mark.parametrize(
    ("content", "expected_error"),
    [
        pytest.param({}, "Missing required field: `queries`", id="empty"),
    ],
)
def test_parse_query_file_content_error(
    content: dict[str, object], expected_error: str
) -> None:
    with pytest.raises(QueryFileContentParserError) as error:
        parse_query_file_content(query_file_content=content)

    assert error.value.error == expected_error


@pytest.mark.parametrize(
    ("path_str"),
    [
        pytest.param("/kek"),
        pytest.param("/"),
    ],
)
def test_validate_path_not_raised_error(path_str: str):
    create_path_object_from_str(path_str=path_str)
