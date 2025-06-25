import logging
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Annotated, Literal

from cyclopts import App
from cyclopts import Parameter as CycloptsParameter

from strictql_postgres.config_manager import (
    GetStrictQLQueriesToGenerateError,
    ParsedPyprojectTomlWithStrictQLSection,
    ParseTomlFileAsModelError,
    QueryFileContentModel,
    get_strictql_queries_to_generate,
    parse_toml_file_as_model,
)
from strictql_postgres.queries_generator import StrictqlGeneratorError, generate_queries

logger = logging.getLogger(__name__)


app = App()


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def generate_from_config() -> None:
    """
    Сгенерировать код для выполнения sql-запросов в Postgres.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """

    pyproject_toml_path = pathlib.Path("pyproject.toml").resolve()

    try:
        parsed_pyproject_file_with_strictql_settings = parse_toml_file_as_model(
            path=pyproject_toml_path, model_type=ParsedPyprojectTomlWithStrictQLSection
        )
    except ParseTomlFileAsModelError:
        logger.exception(f"Error occurred while parsing {pyproject_toml_path} file")
        exit(1)

    parsed_strictql_settings = (
        parsed_pyproject_file_with_strictql_settings.tool.strictql_postgres
    )
    parsed_query_files = {}
    for query_file in parsed_strictql_settings.query_files_path:
        query_file_path = pathlib.Path(query_file).resolve()

        try:
            parsed_query_file_content = parse_toml_file_as_model(
                path=query_file_path, model_type=QueryFileContentModel
            )
        except ParseTomlFileAsModelError:
            logger.exception(
                f"Error occurred while parsing query file: `{query_file_path}`"
            )
            sys.exit(1)

        parsed_query_files[query_file_path] = parsed_query_file_content.queries
    try:
        queries_to_generate = get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path=parsed_query_files,
            code_generated_dir=parsed_strictql_settings.code_generate_dir,
            parsed_databases=parsed_strictql_settings.databases,
            environment_variables=os.environ,
        )
    except GetStrictQLQueriesToGenerateError:
        logger.exception(
            "Error occurred while collecting quiries to generate from parsed configs"
        )
        sys.exit(1)

    try:
        await generate_queries(queries_to_generate)
    except StrictqlGeneratorError as error:
        logger.error(error)
        sys.exit(1)


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def generate(
    query: str,
    function_name: str,
    param_names: list[str] | None = None,
    fetch_type: Literal["fetch_all", "execute", "fetch_row"] = "fetch_all",
    dry_run: Annotated[
        bool,
        CycloptsParameter(
            negative="", help="Вывести результат в stdout, не создавать файлы"
        ),
    ] = False,
) -> None:
    """
    Сгенерировать код для выполнения sql-запросов в Postgres.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """
    pass
    # async with asyncpg.create_pool(
    #     host="127.0.0.1",
    #     user="postgres",
    #     password="password",
    #     port=5432,
    #     database="postgres",
    # ) as connection_pool:
    #     async with connection_pool.acquire() as connection:
    #         prepared_statement = await connection.prepare(query=query)
    #
    #         schema = get_pg_response_schema_from_prepared_statement(
    #             prepared_stmt=prepared_statement,
    #         )
    #
    #         param_types = await get_bind_params_python_types(
    #             prepared_statement=prepared_statement,
    #         )
    #         params = []
    #         if param_names:
    #             for index, parameter_type in enumerate(param_types):
    #                 params.append(
    #                     BindParam(
    #                         name_in_function=param_names[index],
    #                         type_=parameter_type.type_,
    #                         is_optional=parameter_type.is_optional,
    #                     )
    #                 )
    # match fetch_type:
    #     case "fetch_all":
    #         print(
    #             await generate_code_for_query_with_fetch_all_method(
    #                 query=query,
    #                 result_schema=NotEmptyRowSchema(schema=schema),
    #                 bind_params=params,
    #                 function_name=StringInSnakeLowerCase(function_name),
    #                 code_quality_improver=CodeQualityImprover(
    #                     mypy_runner=MypyRunner(mypy_path=pathlib.Path(__file__).parent)
    #                 ),
    #             )
    #         )
    #     case "execute":
    #         print(
    #             await generate_code_for_query_with_execute_method(
    #                 query=query,
    #                 bind_params=params,
    #                 function_name=StringInSnakeLowerCase(function_name),
    #                 code_quality_improver=CodeQualityImprover(
    #                     mypy_runner=MypyRunner(mypy_path=pathlib.Path(__file__).parent)
    #                 ),
    #             )
    #         )
    #
    #     case "_":
    #         raise NotImplementedError()


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def check() -> None:
    """
    Проверить, что код для выпонления sql-запросов в Postgres находится в актуальном состоянии.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """
    raise NotImplementedError()


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def init() -> None:
    """
    Инициализировать `strictql` в текущей директории.

    Команда в интерактивном режиме выполнит настройку `strictql`.
    """
    raise NotImplementedError()


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def collect(format: Literal["json"]) -> None:
    """
    Собрать все запросы в один файл для проведения инвентаризации.
    """
    raise NotImplementedError()


if __name__ == "__main__":
    app()


@dataclass
class Config:
    pass


def read_config(path: pathlib.Path) -> Config:
    raise NotImplementedError()
