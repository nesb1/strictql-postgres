import logging
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Annotated, Literal

import tomllib
from cyclopts import App
from cyclopts import Parameter as CycloptsParameter

from strictql_postgres.new_config_manager import (
    ParsedStrictqlSettings,
    PyprojectToolsModel,
    QueryFileContentModel,
    get_strictql_queries_to_generate,
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

    pyproject_toml_text = pathlib.Path("pyproject.toml").resolve().read_text()
    pyproject_toml_data_as_dict: dict[str, object] = tomllib.loads(pyproject_toml_text)
    parsed_pyproject_tools = PyprojectToolsModel.model_validate(
        pyproject_toml_data_as_dict
    )
    if "strictql_postgres" not in parsed_pyproject_tools.tool:
        raise Exception("strictql postgres not exists in pyproject.toml tools section")

    parsed_strictql_settings = ParsedStrictqlSettings.model_validate(
        parsed_pyproject_tools.tool["strictql_postgres"]
    )

    parsed_query_files = {}
    for query_file in parsed_strictql_settings.query_files_path:
        query_file_path = pathlib.Path(query_file)
        if not query_file_path.exists():
            raise Exception(f"Query file not found: {query_file_path}")

        query_file_content = query_file_path.read_text()
        query_file_content_as_dict: dict[str, object] = tomllib.loads(
            query_file_content
        )

        parsed_query_file_content = QueryFileContentModel.model_validate(
            query_file_content_as_dict
        )

        parsed_query_files[query_file_path] = parsed_query_file_content.queries

    queries_to_generate = get_strictql_queries_to_generate(
        parsed_queries_to_generate_by_query_file_path=parsed_query_files,
        code_generated_dir=parsed_strictql_settings.code_generate_dir,
        parsed_databases=parsed_strictql_settings.databases,
        environment_variables=os.environ,
    )

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
