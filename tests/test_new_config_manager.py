import pathlib

import pytest
from pydantic import SecretStr

from strictql_postgres.new_config_manager import (
    get_strictql_queries_to_generate,
    ParsedQueryToGenerate,
    ParsedParameter,
    ParsedStrictqlSettings,
    ParsedDatabase,
    GetStrictQLQueriesToGenerateError,
)
from strictql_postgres.queries_to_generate import (
    StrictQLQuiriesToGenerate,
    QueryToGenerate,
    Parameter,
)


def test_get_strictql_settings_works():

    code_generation_directory_path = pathlib.Path("generated_code")
    expected = StrictQLQuiriesToGenerate(
        queries_to_generate={
            code_generation_directory_path
            / "file1.py": QueryToGenerate(
                query="select * from table;",
                parameters={
                    "param": Parameter(
                        is_optional=False,
                    )
                },
                database_name="db1",
                database_connection_url=SecretStr("connect_to_postgres1"),
                return_type="list",
            ),
            code_generation_directory_path
            / "file2.py": QueryToGenerate(
                query="select * from table;",
                parameters={
                    "param": Parameter(
                        is_optional=False,
                    )
                },
                database_name="db2",
                database_connection_url=SecretStr("connect_to_postgres2"),
                return_type="list",
            ),
        },
        generated_code_path=code_generation_directory_path,
    )

    actual = get_strictql_queries_to_generate(
        parsed_queries_to_generate={
            pathlib.Path("query_file.toml"): [
                ParsedQueryToGenerate(
                    query="select * from table",
                    parameter_names={
                        "param": ParsedParameter(is_optional=False),
                    },
                    database="db1",
                    return_type="list",
                    relative_path="file1.py",
                ),
                ParsedQueryToGenerate(
                    query="select * from table",
                    parameter_names={
                        "param": ParsedParameter(is_optional=False),
                    },
                    database="db2",
                    return_type="list",
                    relative_path="file2.py",
                ),
            ]
        },
        code_generated_dir=str(code_generation_directory_path),
        databases={
            "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            "db2": ParsedDatabase(env_name_to_read_connection_url="DB2"),
        },
        environment_variables={
            "DB1": "connect_to_postgres1",
            "DB2": "connect_to_postgres2",
        },
    )

    assert actual == expected


def test_get_strictql_settings_not_unique_file_path_in_one_query_file():

    code_generation_directory_path = pathlib.Path("generated_code")

    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:

        query_file_path = pathlib.Path("query_file.toml")
        get_strictql_queries_to_generate(
            parsed_queries_to_generate={
                query_file_path: [
                    ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                    ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                ]
            },
            code_generated_dir=str(code_generation_directory_path),
            databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    assert (
        error.value.error
        == f"Found not unique path for query generation, file_path: `file1.py` in query_files: [{query_file_path.resolve()}]"
    )


def test_get_strictql_settings_not_unique_file_path_in_multiple_query_files():

    code_generation_directory_path = pathlib.Path("generated_code")

    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:

        query_file_path1 = pathlib.Path("query_file1.toml").resolve()
        query_file_path2 = pathlib.Path("query_file2.toml").resolve()

        get_strictql_queries_to_generate(
            parsed_queries_to_generate={
                query_file_path1: [
                    ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                ],
                query_file_path2: [
                    ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                ],
            },
            code_generated_dir=str(code_generation_directory_path),
            databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    assert (
        error.value.error
        == f"Found not unique path for query generation, file_path: `file1.py`"
    )


# todo windows test
# todo тут нужен тест, который проверит что путь потом не поменялся, сейчас тут нет проверки на абсолютный путь как лучше это сделать?


@pytest.mark.parametrize("special_path_symbol", [".", "..", "~"])
def test_get_strictql_settings_raises_error_when_query_contains_special_symbols(
    special_path_symbol: str,
):

    code_generation_directory_path = pathlib.Path("generated_code")

    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:

        query_file = pathlib.Path("query_file")
        get_strictql_queries_to_generate(
            parsed_queries_to_generate={
                query_file: [
                    ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path=special_path_symbol,
                    ),
                ],
            },
            code_generated_dir=str(code_generation_directory_path),
            databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    assert (
        error.value.error
        == f"Found special path symbol: `{special_path_symbol}` in a query to generate path: `{special_path_symbol}`, query_file: `{query_file}`"
    )
