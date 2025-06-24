import pathlib

import pytest
from pydantic import SecretStr

from strictql_postgres.new_config_manager import (
    GetStrictQLQueriesToGenerateError,
    ParsedDatabase,
    ParsedParameter,
    ParsedQueryToGenerate,
    get_strictql_queries_to_generate,
)
from strictql_postgres.queries_to_generate import (
    DataBaseSettings,
    Parameter,
    QueryToGenerate,
    StrictQLQueriesToGenerate,
)


def test_get_strictql_settings_works() -> None:
    code_generation_directory_path = pathlib.Path("generated_code")
    connection_url_to_db1 = SecretStr("connect_to_postgres1")
    connection_url_to_db2 = SecretStr("connect_to_postgres2")
    expected = StrictQLQueriesToGenerate(
        queries_to_generate={
            (code_generation_directory_path / "file1.py").resolve(): QueryToGenerate(
                query="select * from table",
                parameters={
                    "param": Parameter(
                        is_optional=False,
                    )
                },
                database_name="db1",
                database_connection_url=connection_url_to_db1,
                return_type="list",
                function_name="select_all1",
            ),
            (code_generation_directory_path / "file2.py").resolve(): QueryToGenerate(
                query="select * from table",
                parameters={
                    "param": Parameter(
                        is_optional=False,
                    )
                },
                database_name="db2",
                database_connection_url=connection_url_to_db2,
                return_type="list",
                function_name="select_all2",
            ),
        },
        generated_code_path=code_generation_directory_path,
        databases={
            "db1": DataBaseSettings(connection_url=connection_url_to_db1),
            "db2": DataBaseSettings(connection_url=connection_url_to_db2),
        },
    )

    actual = get_strictql_queries_to_generate(
        parsed_queries_to_generate_by_query_file_path={
            pathlib.Path("query_file.toml"): {
                "select_all1": ParsedQueryToGenerate(
                    query="select * from table",
                    parameter_names={
                        "param": ParsedParameter(is_optional=False),
                    },
                    database="db1",
                    return_type="list",
                    relative_path="file1.py",
                ),
                "select_all2": ParsedQueryToGenerate(
                    query="select * from table",
                    parameter_names={
                        "param": ParsedParameter(is_optional=False),
                    },
                    database="db2",
                    return_type="list",
                    relative_path="file2.py",
                ),
            }
        },
        code_generated_dir=str(code_generation_directory_path),
        parsed_databases={
            "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            "db2": ParsedDatabase(env_name_to_read_connection_url="DB2"),
        },
        environment_variables={
            "DB1": connection_url_to_db1.get_secret_value(),
            "DB2": connection_url_to_db2.get_secret_value(),
        },
    )

    assert actual == expected


def test_get_strictql_settings_not_unique_file_path_in_one_query_file() -> None:
    code_generation_directory_path = pathlib.Path("generated_code").resolve()

    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:
        query_file_path = pathlib.Path("query_file.toml")
        get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path={
                query_file_path: {
                    "select_all_1": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                    "select_all_2": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                }
            },
            code_generated_dir=str(code_generation_directory_path),
            parsed_databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    expected_error = f"Found multiple queries to generate with path: `{(code_generation_directory_path / 'file1.py').resolve()}`, queries: {[f'{query_file_path.resolve()}::select_all_1', f'{query_file_path.resolve()}::select_all_2']}"
    assert error.value.error == expected_error


def test_get_strictql_settings_not_unique_file_path_in_multiple_query_files() -> None:
    code_generation_directory_path = pathlib.Path("generated_code")

    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:
        query_file_path1 = pathlib.Path("query_file1.toml").resolve()
        query_file_path2 = pathlib.Path("query_file2.toml").resolve()

        get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path={
                query_file_path1: {
                    "select_all": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                },
                query_file_path2: {
                    "select_all": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="file1.py",
                    ),
                },
            },
            code_generated_dir=str(code_generation_directory_path),
            parsed_databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    expected_error = f"Found multiple queries to generate with path: `{(code_generation_directory_path / 'file1.py').resolve()}`, queries: {[f'{query_file_path1.resolve()}::select_all', f'{query_file_path2.resolve()}::select_all']}"
    assert error.value.error == expected_error


# todo windows test
# todo тут нужен тест, который проверит что путь потом не поменялся, сейчас тут нет проверки на абсолютный путь как лучше это сделать?


@pytest.mark.parametrize("special_path_symbol", [".", "..", "~"])
def test_get_strictql_settings_raises_error_when_query_file_relative_path_contains_special_symbols(
    special_path_symbol: str,
) -> None:
    code_generation_directory_path = pathlib.Path("generated_code")

    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:
        query_file = pathlib.Path("query_file")
        get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path={
                query_file: {
                    "select_all": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path=special_path_symbol,
                    ),
                }
            },
            code_generated_dir=str(code_generation_directory_path),
            parsed_databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    assert (
        error.value.error
        == f"Found special path symbol: `{special_path_symbol}` in a query to generate path: `{special_path_symbol}`, query_file: `{(code_generation_directory_path / query_file).resolve()}`"
    )


def test_get_queries_to_generate_raises_error_if_database_stated_in_query_file_not_exists_in_settings() -> (
    None
):
    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:
        get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path={
                pathlib.Path("query_file"): {
                    "select_all": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db2",
                        return_type="list",
                        relative_path="kek",
                    ),
                }
            },
            code_generated_dir="generated_code",
            parsed_databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={
                "DB1": "connect_to_postgres1",
            },
        )
    assert (
        error.value.error
        == "Database : `db2` in a query: `query_file::select_all` not exists in a strictql settings"
    )


def test_get_queries_to_generate_raises_error_if_database_connection_url_env_not_set() -> (
    None
):
    with pytest.raises(GetStrictQLQueriesToGenerateError) as error:
        get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path={
                pathlib.Path("query_file"): {
                    "select_all": ParsedQueryToGenerate(
                        query="select * from table",
                        parameter_names={
                            "param": ParsedParameter(is_optional=False),
                        },
                        database="db1",
                        return_type="list",
                        relative_path="kek",
                    ),
                }
            },
            code_generated_dir="generated_code",
            parsed_databases={
                "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            },
            environment_variables={},
        )
    assert (
        error.value.error
        == "Environment variable `DB1` with connection url to database: `db1` not set"
    )
