import logging
import pathlib
import sys
from dataclasses import dataclass
from typing import Annotated, Literal

from cyclopts import App, Parameter
from pydantic import SecretStr

from strictql_postgres.config_manager import (
    DataBaseSettings,
    QueryToGenerate,
    StrictqlSettings,
)
from strictql_postgres.queries_generator import StrictqlGeneratorError, generate_queries

logger = logging.getLogger(__name__)

TYPES_MAPPING = {"int4": int, "varchar": str, "text": str}

app = App()


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def generate_from_config() -> None:
    """
    Сгенерировать код для выполнения sql-запросов в Postgres.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """

    # resolve_strictql_settings_from_parsed_settings()

    db = DataBaseSettings(
        name="db1",
        connection_url=SecretStr("postgresql://postgres:password@localhost/postgres"),
    )
    settings = StrictqlSettings(
        queries_to_generate={
            pathlib.Path("select_kek.py"): QueryToGenerate(
                query="select * from testdt where dt6 > $1;",
                name="select from testdt",
                parameter_names=["dt6"],
                database=db,
                return_type="list",
                function_name="select_dt",
            ),
        },
        databases={"db1": db},
        generated_code_path=pathlib.Path("strictql_postgres/generated_code"),
    )
    try:
        await generate_queries(settings)
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
        Parameter(negative="", help="Вывести результат в stdout, не создавать файлы"),
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
