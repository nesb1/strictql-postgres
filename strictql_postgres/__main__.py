import pathlib
from dataclasses import dataclass

from cyclopts import App, Parameter
from typing import Annotated, Literal

from strictql_postgres.code_generator import generate_code_for_query, QueryWithDBInfo
from strictql_postgres.code_quality import CodeQualityImprover, MypyRunner
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase

app = App()


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def generate(
    dry_run: Annotated[
        bool,
        Parameter(negative="", help="Вывести результат в stdout, не создавать файлы"),
    ] = False,
) -> None:
    """
    Сгенерировать код для выполнения sql-запросов в Postgres.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """

    print(
        await generate_code_for_query(
            query_with_db_info=QueryWithDBInfo(
                query="select 1 as v", query_result_row_model={"v": int}
            ),
            execution_variant="fetch_all",
            function_name=StringInSnakeLowerCase("select_1"),
            code_quality_improver=CodeQualityImprover(
                mypy_runner=MypyRunner(mypy_path=pathlib.Path(__file__).parent)
            ),
        )
    )


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
