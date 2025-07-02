import pathlib
from tempfile import TemporaryDirectory

from pydantic import SecretStr

from strictql_postgres.queries_generator import (
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
        file_1 = generated_code_dir_path / pathlib.Path("query1.py")
        file_2 = generated_code_dir_path / pathlib.Path("query2.py")
        files = await generate_queries(
            queries_to_generate=StrictQLQueriesToGenerate(
                queries_to_generate={
                    file_1: QueryToGenerate(
                        query="select 1 as value",
                        parameters={},
                        database_name="db",
                        database_connection_url=db_connection_url,
                        query_type="fetch",
                        function_name=StringInSnakeLowerCase("query"),
                    ),
                    file_2: QueryToGenerate(
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

        assert file_1 in files
        assert file_1 in files


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
