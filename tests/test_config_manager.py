import os
import pathlib
import tempfile
from contextlib import contextmanager
from typing import AsyncIterator, Iterator

import pytest
from mypy.util import orjson
from pydantic import SecretStr

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
    resolve_strictql_settings,
    StrictqlSettings,
    get_strictql_settings,
    QueryToGenerate,
    Parameter,
    DataBaseSettings,
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


#
#
# def test_resolve_strictql_settings_works() -> None:
#     with tempfile.TemporaryDirectory() as tmpdir:
#
#         resolve_strictql_settings(
#             code_generation_directory=pathlib.Path(tmpdir),
#             parsed_query_files=[ParsedQueryToGenerate(query="select * from table",
#                                                       )],
#         )
#
# def test_resolve_strictql_settings_raises_error() -> None:
#     pass
#
#


@contextmanager
def tmp_set_envs(envs: dict[str, str]) -> Iterator[None]:
    current_envs = {env_name: os.environ.get(env_name) for env_name in envs.keys()}

    try:
        os.environ.update(envs)
        yield
    finally:
        os.environ.update(current_envs)


def test_get_strictql_settings_works() -> None:
    with tempfile.TemporaryDirectory(suffix="tmp_project") as tmp_project:
        tmp_project_path = pathlib.Path(tmp_project)

        code_generation_dir = tmp_project_path / "code_generation_dir"
        code_generation_dir.mkdir(exist_ok=False)

        pyproject_toml_path = tmp_project_path / "pyproject.toml"

        query_file1_path = tmp_project_path / "query_file1.toml"
        query_file2_path = tmp_project_path / "query_file2.toml"

        databases = {
            "TEST_DB_ENV1": DataBaseSettings(
                connection_url=SecretStr(
                    "postgresql://postgres:password@localhost/postgres"
                ),
            ),
            "TEST_DB_ENV2": DataBaseSettings(
                connection_url=SecretStr(
                    "postgresql://postgres:password@localhost/postgres"
                ),
            ),
        }

        pyproject_toml_path.write_text(
            data=f"""
            [tool.strictql_postgres]
            code_generate_dir="{code_generation_dir}
            query_files_path=[{query_file1_path}, {query_file2_path}]
            databases={{
            "db1" = {{"env_name_to_read_connection_url" = "TEST_DB_ENV1"}}
            "db2" = {{"env_name_to_read_connection_url" = "TEST_DB_ENV2"}}
            }}
            """
        )

        query_file1_path.write_text(
            data=f"""
            [queries.get_user_by_id]
            query = "select * from user where id = $1"
            parameter_names = {{ param1 = {{ is_optional = true }} }}
            database = "db1"
            return_type = "list"
            
            [queries.get_users]
            query = "select * from user"
            database = "db2"
            return_type = "list"
"""
        )

        query_file2_path.write_text(
            data=f"""
                    [queries.select_order]
                    query = "select * from order limit 1"
                    database = "db2"
                    return_type = "list"
        """
        )

        with tmp_set_envs(
            envs={
                env_name: db.connection_url.get_secret_value()
                for env_name, db in databases.items()
            }
        ):
            actual_settings = get_strictql_settings(
                pyproject_toml_path=pyproject_toml_path
            )

    expected_settings = StrictqlSettings(
        queries_to_generate={
            query_file1_path: [
                QueryToGenerate(
                    query="select * from user where id = $1",
                    parameter_names={"param1": Parameter(is_optional=True)},
                    database_name="db1",
                    database_connection_url=databases["TEST_DB_ENV1"].connection_url,
                    return_type="list",
                    function_name="get_user_by_id",
                ),
                QueryToGenerate(
                    query="select * from user",
                    parameter_names={},
                    database_name="db2",
                    database_connection_url=databases["TEST_DB_ENV2"].connection_url,
                    return_type="list",
                    function_name="get_users",
                ),
            ],
            query_file2_path: [
                QueryToGenerate(
                    query="select * from order limit 1",
                    parameter_names={},
                    database_name="db2",
                    database_connection_url=databases["TEST_DB_ENV2"].connection_url,
                    return_type="list",
                    function_name="select_order",
                ),
            ],
        },
        databases={
            "db1": DataBaseSettings(
                connection_url=databases["TEST_DB_ENV1"].connection_url,
            ),
            "db2": DataBaseSettings(
                connection_url=databases["TEST_DB_ENV2"].connection_url,
            ),
        },
        generated_code_path=code_generation_dir,
    )

    assert expected_settings == actual_settings