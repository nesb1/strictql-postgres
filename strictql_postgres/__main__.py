import logging
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Literal

from cyclopts import App

from strictql_postgres.config_manager import (
    GetStrictQLQueriesToGenerateError,
    ParsedPyprojectTomlWithStrictQLSection,
    ParseTomlFileAsModelError,
    QueryFileContentModel,
    get_strictql_queries_to_generate,
    parse_toml_file_as_model,
)
from strictql_postgres.dir_diff import get_missed_files, get_diff_for_changed_files
from strictql_postgres.directory_reader import read_directory_python_files_recursive
from strictql_postgres.generated_code_writer import (
    GeneratedCodeWriterError,
    write_generated_code,
)
from strictql_postgres.meta_file import STRICTQL_META_FILE_NAME
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
        files = await generate_queries(queries_to_generate)
    except StrictqlGeneratorError as error:
        logger.error(error.error)
        sys.exit(1)

    try:
        write_generated_code(
            target_directory=queries_to_generate.generated_code_path,
            files=files,
            meta_file_name=STRICTQL_META_FILE_NAME,
        )
    except GeneratedCodeWriterError as error:
        logger.exception(
            f"Error occurred while writing generated code to disk, error: {error.error}"
        )
        sys.exit(1)


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def check() -> None:
    """
    Проверить, что код для выпонления sql-запросов в Postgres находится в актуальном состоянии.

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
        files_to_generate = await generate_queries(queries_to_generate)
    except StrictqlGeneratorError as error:
        logger.error(error.error)
        sys.exit(1)

    actual_files = read_directory_python_files_recursive(
        path=queries_to_generate.generated_code_path
    )

    missed_files = get_missed_files(actual=actual_files, expected=files_to_generate)
    if missed_files:
        print("missed files:")
        for missed_file in missed_files:
            print(f"- {missed_file.resolve()}")

    extra_files = get_missed_files(actual=files_to_generate, expected=actual_files)
    if extra_files:
        print("extra files:")
        for extra_file in extra_files:
            print(f"- {extra_file.resolve()}")

    diff_for_changed_files = get_diff_for_changed_files(
        actual=actual_files, expected=files_to_generate
    )
    if diff_for_changed_files:
        print("Changed files:")
        for file_path, diff_for_changed_file in diff_for_changed_files.items():
            print(f"- {file_path.resolve()}")
            print(diff_for_changed_file)
            print("\n")


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
