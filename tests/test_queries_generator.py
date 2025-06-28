import pathlib
from tempfile import TemporaryDirectory

import pytest
from pydantic import SecretStr

from strictql_postgres.meta_file import generate_meta_file
from strictql_postgres.queries_generator import (
    STRICTQL_META_FILE_NAME,
    StrictqlGeneratorError,
    generate_queries,
)
from strictql_postgres.queries_to_generate import (
    DataBaseSettings,
    QueryToGenerate,
    StrictQLQueriesToGenerate,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase


async def test_strictql_generator_works() -> None:
    with TemporaryDirectory() as tmpdir:
        generated_code_dir_path = pathlib.Path(tmpdir) / "generated_code_dir"
        db_connection_url = SecretStr(
            "postgresql://postgres:password@localhost/postgres"
        )
        await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={
                    generated_code_dir_path
                    / pathlib.Path("query1.py"): QueryToGenerate(
                        query="select 1 as value",
                        parameters={},
                        database_name="db",
                        database_connection_url=db_connection_url,
                        query_type="fetch",
                        function_name=StringInSnakeLowerCase("query"),
                    ),
                    generated_code_dir_path
                    / pathlib.Path("query2.py"): QueryToGenerate(
                        query="select 2 as value",
                        parameters={},
                        database_name="db",
                        database_connection_url=db_connection_url,
                        query_type="fetch",
                        function_name=StringInSnakeLowerCase("query"),
                    ),
                },
                databases={"db": DataBaseSettings(connection_url=db_connection_url)},
                generated_code_path=generated_code_dir_path,
            )
        )

        file_names = {file.name for file in generated_code_dir_path.iterdir()}

        assert file_names == {"query1.py", "query2.py", STRICTQL_META_FILE_NAME}


async def test_strictql_generator_supports_subdirectories() -> None:
    db_connection_url = SecretStr("postgresql://postgres:password@localhost/postgres")

    with TemporaryDirectory() as tmpdir:
        generated_code_dir_path = pathlib.Path(tmpdir) / "generated_code_dir"
        relative_path = pathlib.Path("subdir") / "subdir" / "file.py"
        await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={
                    generated_code_dir_path / relative_path: QueryToGenerate(
                        query="select 1 as value",
                        parameters={},
                        database_name="db",
                        database_connection_url=db_connection_url,
                        query_type="fetch",
                        function_name=StringInSnakeLowerCase("query"),
                    ),
                },
                databases={"db": DataBaseSettings(connection_url=db_connection_url)},
                generated_code_path=generated_code_dir_path,
            )
        )
        (generated_code_dir_path / generated_code_dir_path).exists()


async def test_strictql_generator_creates_generated_code_dir_if_it_does_not_exists() -> (
    None
):
    db_connection_url = SecretStr("postgresql://postgres:password@localhost/postgres")

    with TemporaryDirectory() as tmpdir:
        generated_code_dir_path = pathlib.Path(tmpdir) / "generated_code_dir"
        assert not generated_code_dir_path.exists()
        await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={
                    generated_code_dir_path
                    / pathlib.Path("query1.py"): QueryToGenerate(
                        query="select 1 as value",
                        parameters={},
                        database_name="db",
                        database_connection_url=db_connection_url,
                        query_type="fetch",
                        function_name=StringInSnakeLowerCase("query"),
                    ),
                },
                databases={"db": DataBaseSettings(connection_url=db_connection_url)},
                generated_code_path=generated_code_dir_path,
            )
        )

        file_names = {file.name for file in generated_code_dir_path.iterdir()}

        assert file_names == {"query1.py", STRICTQL_META_FILE_NAME}

        meta_file_path = generated_code_dir_path / STRICTQL_META_FILE_NAME
        meta_file_content = meta_file_path.read_text()

        expected_meta_file_content = generate_meta_file(
            generated_code_dir_path, meta_file_name=meta_file_path.name
        )

        assert meta_file_content == expected_meta_file_content.model_dump_json()


async def test_strictql_generator_recreate_generated_code_dir_if_existence_code_dir_equals_to_meta_file_content() -> (
    None
):
    db_connection_url = SecretStr("postgresql://postgres:password@localhost/postgres")

    with TemporaryDirectory() as tmpdir:
        generated_code_dir_path = pathlib.Path(tmpdir) / "generated_code_dir"
        generated_code_dir_path.mkdir()
        file_path = generated_code_dir_path / "query1.py"
        file_path.write_text("some text")

        meta_file_content = generate_meta_file(
            path=generated_code_dir_path, meta_file_name=STRICTQL_META_FILE_NAME
        )
        (generated_code_dir_path / STRICTQL_META_FILE_NAME).write_text(
            meta_file_content.model_dump_json()
        )

        await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={
                    generated_code_dir_path
                    / pathlib.Path("query1.py"): QueryToGenerate(
                        query="select 1 as value",
                        parameters={},
                        database_name="db",
                        database_connection_url=db_connection_url,
                        query_type="fetch",
                        function_name=StringInSnakeLowerCase("query"),
                    ),
                },
                databases={"db": DataBaseSettings(connection_url=db_connection_url)},
                generated_code_path=generated_code_dir_path,
            )
        )

        file_names = {file.name for file in generated_code_dir_path.iterdir()}

        assert file_names == {"query1.py", STRICTQL_META_FILE_NAME}


async def test_strictql_generator_raises_error_if_generated_code_directory_exists_without_meta_file_content() -> (
    None
):
    db_connection_url = SecretStr("postgresql://postgres:password@localhost/postgres")

    with TemporaryDirectory() as tmpdir:
        generated_code_dir_path = pathlib.Path(tmpdir) / "generated_code_dir"
        generated_code_dir_path.mkdir()
        file_path = generated_code_dir_path / "query1.py"
        file_path.write_text("some text")

        with pytest.raises(StrictqlGeneratorError) as error:
            await generate_queries(
                queries_to_generate=StrictQLQueriesToGenerate(
                    queries_to_generate={
                        generated_code_dir_path
                        / pathlib.Path("query1.py"): QueryToGenerate(
                            query="select 1 as value",
                            parameters={},
                            database_name="db",
                            database_connection_url=db_connection_url,
                            query_type="fetch",
                            function_name=StringInSnakeLowerCase("query"),
                        ),
                    },
                    databases={
                        "db": DataBaseSettings(connection_url=db_connection_url)
                    },
                    generated_code_path=generated_code_dir_path,
                )
            )

        assert (
            error.value.error
            == f"Generated code directory: `{generated_code_dir_path.resolve()}` already exists and does not contain a meta file {STRICTQL_META_FILE_NAME}."
            f" You probably specified the wrong directory or deleted the meta file. If you deleted the meta file yourself, then you need to manually delete the directory and regenerate the code."
        )


async def test_strictql_generator_raises_error_if_generated_code_directory_exists_with_not_equals_meta_file_content() -> (
    None
):
    db_connection_url = SecretStr("postgresql://postgres:password@localhost/postgres")

    with TemporaryDirectory() as tmpdir:
        generated_code_dir_path = pathlib.Path(tmpdir) / "generated_code_dir"
        generated_code_dir_path.mkdir()
        file_path = generated_code_dir_path / "query1.py"
        file_path.write_text("some text")

        meta_file_content = generate_meta_file(
            path=generated_code_dir_path, meta_file_name=STRICTQL_META_FILE_NAME
        )
        (generated_code_dir_path / STRICTQL_META_FILE_NAME).write_text(
            meta_file_content.model_dump_json()
        )

        another_file_path = generated_code_dir_path / "query2.py"
        another_file_path.write_text("some text 123")

        with pytest.raises(StrictqlGeneratorError) as error:
            await generate_queries(
                queries_to_generate=StrictQLQueriesToGenerate(
                    queries_to_generate={
                        generated_code_dir_path
                        / pathlib.Path("query1.py"): QueryToGenerate(
                            query="select 1 as value",
                            parameters={},
                            database_name="db",
                            database_connection_url=db_connection_url,
                            query_type="fetch",
                            function_name=StringInSnakeLowerCase("query"),
                        ),
                    },
                    databases={
                        "db": DataBaseSettings(connection_url=db_connection_url)
                    },
                    generated_code_path=generated_code_dir_path,
                )
            )

        assert (
            error.value.error
            == f"Generated code directory: `{generated_code_dir_path.resolve()}` already exists and generated files in it are not equals to meta file content {STRICTQL_META_FILE_NAME}, looks like generated has been changed manually."
            f" Delete the generated code directory and regenerate the code."
        )


#
# async def test_strictql_generator_handle_query_generator_error() -> None:
#     data_base = DataBaseSettings(
#         name="test",
#         connection_url=SecretStr("postgresql://postgres:password@localhost/postgres"),
#     )
#     with TemporaryDirectory() as tmpdir:
#         generated_code_dir_path = pathlib.Path(tmpdir)
#         existing_file = "file.py"
#         (generated_code_dir_path / existing_file).touch(exist_ok=False)
#
#         with mock.patch(
#             "strictql_postgres.queries_generator.generate_query_python_code",
#             new=AsyncMock(),
#         ) as mocked_generate_query_python_code:
#             mocked_generate_query_python_code.side_effect = [  # type: ignore[misc]
#                 "a=1",
#                 QueryPythonCodeGeneratorError("123"),
#                 Exception("exception"),
#             ]
#             with pytest.raises(StrictqlGeneratorError):
#                 await generate_queries(
#                     settings=StrictqlSettings(
#                         queries_to_generate={
#                             pathlib.Path("query1.py"): QueryToGenerate(
#                                 query="select 1 as value",
#                                 name="query1",
#                                 parameter_names=[],
#                                 database=data_base,
#                                 return_type="list",
#                                 function_name="select_1",
#                             ),
#                             pathlib.Path("query2.py"): QueryToGenerate(
#                                 query="select 1 as value",
#                                 name="query1",
#                                 parameter_names=[],
#                                 database=data_base,
#                                 return_type="list",
#                                 function_name="select_1",
#                             ),
#                         },
#                         databases={data_base.name: data_base},
#                         generated_code_path=generated_code_dir_path,
#                     )
#                 )
#
#         file_names = [file.name for file in generated_code_dir_path.iterdir()]
#
#         assert file_names == [existing_file]
#
#
# async def test_strictql_generator_handle_query_generator_error_immediately() -> None:
#     data_base = DataBaseSettings(
#         name="test",
#         connection_url=SecretStr("postgresql://postgres:password@localhost/postgres"),
#     )
#     with TemporaryDirectory() as tmpdir:
#         generated_code_dir_path = pathlib.Path(tmpdir)
#         existing_file = "file.py"
#         (generated_code_dir_path / existing_file).touch(exist_ok=False)
#
#         called = False
#
#         async def long_running_task(*args: object, **kwargs: object) -> str:
#             nonlocal called
#
#             if not called:
#                 called = True
#                 raise QueryPythonCodeGeneratorError("123")
#
#             await asyncio.sleep(1)
#             return "a=1"
#
#         with mock.patch(
#             "strictql_postgres.queries_generator.generate_query_python_code",
#             new=AsyncMock(),
#         ) as mocked_generate_query_python_code:
#             mocked_generate_query_python_code.side_effect = long_running_task
#             with pytest.raises(StrictqlGeneratorError):
#                 async with asyncio.timeout(0.5):
#                     await generate_queries(
#                         settings=StrictqlSettings(
#                             queries_to_generate={
#                                 pathlib.Path("query1.py"): QueryToGenerate(
#                                     query="select 1 as value",
#                                     name="query1",
#                                     parameter_names=[],
#                                     database=data_base,
#                                     return_type="list",
#                                     function_name="select_1",
#                                 ),
#                                 pathlib.Path("query2.py"): QueryToGenerate(
#                                     query="select 1 as value",
#                                     name="query1",
#                                     parameter_names=[],
#                                     database=data_base,
#                                     return_type="list",
#                                     function_name="select_1",
#                                 ),
#                             },
#                             databases={data_base.name: data_base},
#                             generated_code_path=generated_code_dir_path,
#                         )
#                     )
#
#         file_names = [file.name for file in generated_code_dir_path.iterdir()]
#
#         assert file_names == [existing_file]
#
#
# async def test_strictql_generator_handle_invalid_postgres_url() -> None:
#     data_base = DataBaseSettings(
#         name="test",
#         connection_url=SecretStr("invalid_postgres_url"),
#     )
#     with TemporaryDirectory() as tmpdir:
#         generated_code_dir_path = pathlib.Path(tmpdir)
#
#         with pytest.raises(StrictqlGeneratorError):
#             await generate_queries(
#                 settings=StrictqlSettings(
#                     queries_to_generate={
#                         pathlib.Path("query1.py"): QueryToGenerate(
#                             query="select 1 as value",
#                             name="query1",
#                             parameter_names=[],
#                             database=data_base,
#                             return_type="list",
#                             function_name="select_1",
#                         ),
#                     },
#                     databases={data_base.name: data_base},
#                     generated_code_path=generated_code_dir_path,
#                 )
#             )
#
#
# async def test_strictql_generator_handle_invalid_postgres_login_password() -> None:
#     data_base = DataBaseSettings(
#         name="test",
#         connection_url=SecretStr(
#             "postgresql://postgres:invalid_password@localhost/postgres"
#         ),
#     )
#     with TemporaryDirectory() as tmpdir:
#         generated_code_dir_path = pathlib.Path(tmpdir)
#
#         with pytest.raises(StrictqlGeneratorError):
#             await generate_queries(
#                 settings=StrictqlSettings(
#                     queries_to_generate={
#                         pathlib.Path("query1.py"): QueryToGenerate(
#                             query="select 1 as value",
#                             name="query1",
#                             parameter_names=[],
#                             database=data_base,
#                             return_type="list",
#                             function_name="select_1",
#                         ),
#                     },
#                     databases={data_base.name: data_base},
#                     generated_code_path=generated_code_dir_path,
#                 )
#             )
