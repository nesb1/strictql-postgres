import pathlib
from dataclasses import dataclass

from cyclopts import App, Parameter
from typing import Annotated, Literal

import asyncpg
from strictql_postgres.code_generator import (
    generate_code_for_query,
)
from strictql_postgres.common_types import QueryParam, QueryWithDBInfo, SelectQuery
from strictql_postgres.code_quality import CodeQualityImprover, MypyRunner
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.pg_bind_params_type_getter import (
    get_bind_params_python_types_from_prepared_statement,
)

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
    query = "select * from users where id = $1"
    select_query = SelectQuery(query=query)
    params_mapping = ["user_id"]
    row_model = {"id": int, "name": str}
    async with asyncpg.create_pool(
        host="127.0.0.1",
        user="postgres",
        password="password",
        port=5432,
        database="postgres",
    ) as connection_pool:
        async with connection_pool.acquire() as connection:
            prepared_statement = await connection.prepare(query=select_query.query)
            print("prepared statement")
            param_types = get_bind_params_python_types_from_prepared_statement(
                prepared_statement=prepared_statement,
                python_type_by_postgres_type={"int4": int, "varchar": str},
            )
            params = []
            for index, parameter_type in enumerate(param_types):
                params.append(
                    QueryParam(
                        name_in_function=params_mapping[index], type_=parameter_type
                    )
                )

    print(
        await generate_code_for_query(
            query_with_db_info=QueryWithDBInfo(
                query=select_query,
                result_row_model=row_model,
                params=params,
            ),
            execution_variant="fetch_all",
            function_name=StringInSnakeLowerCase("select_users"),
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
