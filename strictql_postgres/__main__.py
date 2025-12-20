import dataclasses
import logging
import os
import pathlib
import sys

import questionary
from cyclopts import App
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

from strictql_postgres.config_generator import (
    generate_strictql_section_to_pyproject_toml,
)
from strictql_postgres.config_manager import (
    GetStrictQLQueriesToGenerateError,
    ParsedPyprojectTomlWithStrictQLSection,
    ParseTomlFileAsModelError,
    QueryFileContentModel,
    get_strictql_queries_to_generate,
    parse_toml_file_as_model,
)
from strictql_postgres.dir_diff import get_diff_for_changed_files, get_missed_files
from strictql_postgres.directory_reader import read_directory_python_files_recursive
from strictql_postgres.generated_code_writer import (
    GeneratedCodeWriterError,
    write_generated_code,
)
from strictql_postgres.meta_file import (
    FILE_EXTENSIONS_TO_EXCLUDE,
    STRICTQL_META_FILE_NAME,
    generate_meta_file,
)
from strictql_postgres.python_types import FilesContentByPath
from strictql_postgres.queries_generator import (
    PostgresConnectionError,
    QueriesGeneratorErrors,
    generate_queries,
)
from strictql_postgres.queries_to_generate import StrictQLQueriesToGenerate

logger = logging.getLogger(__name__)

console = Console()
app = App(console=console)


@dataclasses.dataclass(frozen=True)
class GenerateQueriesResult:
    queries_to_generate: StrictQLQueriesToGenerate
    generated_code: FilesContentByPath


RESOLVED_PYPROJECT_TOML_PATH = pathlib.Path("pyproject.toml").resolve()


async def _generate_queries() -> GenerateQueriesResult:
    try:
        parsed_pyproject_file_with_strictql_settings = parse_toml_file_as_model(
            path=RESOLVED_PYPROJECT_TOML_PATH,
            model_type=ParsedPyprojectTomlWithStrictQLSection,
        )
    except ParseTomlFileAsModelError as error:
        console.print(
            f"Error occurred while parsing the {RESOLVED_PYPROJECT_TOML_PATH} file. Error: {error.error}",
            style=Style(color="red", bold=True),
        )
        console.print_exception()
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
            console.print(
                f"Error occurred while parsing query file: `{query_file_path}`",
                style=Style(color="red", bold=True),
            )
            console.print_exception()
            sys.exit(1)

        parsed_query_files[query_file_path] = parsed_query_file_content.queries

    if len(parsed_query_files) == 0 and not any(
        (
            parsed_queries
            for parsed_queries in parsed_query_files.values()
            if len(parsed_queries) > 0
        )
    ):
        console.print(
            "There are no specified queries to generate", style=Style(color="yellow")
        )
        sys.exit(1)

    try:
        queries_to_generate = get_strictql_queries_to_generate(
            parsed_queries_to_generate_by_query_file_path=parsed_query_files,
            code_generated_dir=parsed_strictql_settings.code_generate_dir,
            parsed_databases=parsed_strictql_settings.databases,
            environment_variables=os.environ,
        )
    except GetStrictQLQueriesToGenerateError:
        console.print(
            "Error occurred while collecting queries to generate from parsed configs",
            style=Style(color="red", bold=True),
        )
        console.print_exception()
        sys.exit(1)

    console.print(
        f"Generating code for {len(queries_to_generate.queries_to_generate)} queries...",
        style=Style(color="green"),
    )
    try:
        generated_code = await generate_queries(queries_to_generate)
    except PostgresConnectionError as error:
        text = Text(
            f"Error occurred while connecting to database `{error.database}`:\n",
            style=Style(color="red", bold=True),
        )
        error_text = Text(
            error.error,
            style=Style(
                color="black",
                bold=False,
            ),
        )
        console.print(
            text + error_text,
        )
        sys.exit(1)
    except QueriesGeneratorErrors as error:
        console.print(
            f"Error occurred for {len(error.errors)} queries",
            style=Style(color="red", bold=True),
        )
        table = Table("query", "error", show_lines=True, show_edge=True)
        for query_generate_error in error.errors:
            table.add_row(
                Text(
                    query_generate_error.query_to_generate.query,
                    style=Style(color="blue", bold=True),
                ),
                Text(query_generate_error.error),
            )

        console.print(table)
        sys.exit(1)

    return GenerateQueriesResult(
        queries_to_generate=queries_to_generate, generated_code=generated_code
    )


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def generate() -> None:
    """
    Сгенерировать код для выполнения sql-запросов в Postgres.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """
    generate_queries_result = await _generate_queries()
    try:
        write_generated_code(
            target_directory=generate_queries_result.queries_to_generate.generated_code_path,
            files=generate_queries_result.generated_code,
            meta_file_name=STRICTQL_META_FILE_NAME,
        )
    except GeneratedCodeWriterError:
        console.print(
            "Error occurred while writing generated code to disk",
            style=Style(color="red", bold=True),
        )
        console.print_exception()
        sys.exit(1)

    console.print(
        "Code generation completed successfully.",
        style=Style(color="green", bold=True),
    )


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
async def check() -> None:
    """
    Проверить, что код для выпонления sql-запросов в Postgres находится в актуальном состоянии.

    Команда будет искать настройки `strictql` в файле `pyproject.toml`, если файла или настроек нет, то произойдет ошибка.
    """

    generate_queries_result = await _generate_queries()

    actual_files = read_directory_python_files_recursive(
        path=generate_queries_result.queries_to_generate.generated_code_path
    )

    missed_files = get_missed_files(
        actual=actual_files, expected=generate_queries_result.generated_code
    )

    if missed_files:
        missed_files_table = Table(style=Style(color="red"))
        missed_files_table.add_column("File", justify="center")
        for missed_file in missed_files:
            missed_files_table.add_row(str(missed_file))

        console.print("Missed files:", missed_files_table)

    extra_files = get_missed_files(
        actual=generate_queries_result.generated_code, expected=actual_files
    )
    if extra_files:
        extra_files_table = Table(style=Style(color="red"))
        extra_files_table.add_column("File", justify="center")
        for extra_file in extra_files:
            extra_files_table.add_row(str(extra_file))
        console.print("Extra files:", extra_files_table)

    diff_for_changed_files = get_diff_for_changed_files(
        actual=actual_files, expected=generate_queries_result.generated_code
    )

    if diff_for_changed_files:
        console.print(
            f"{len(diff_for_changed_files)} files changed",
            style=Style(color="red", bold=True),
        )
        for file_path, diff_for_changed_file in diff_for_changed_files.items():
            console.print(f"- {file_path.resolve()}")
            for row in diff_for_changed_file.splitlines():
                if row.startswith("-"):
                    console.print(Text(text=row, style=Style(color="red")))
                elif row.startswith("+"):
                    console.print(Text(text=row, style=Style(color="green")))
                else:
                    console.print(row)
            console.print("\n")
    if len(extra_files) > 0 or len(missed_files) > 0 or len(diff_for_changed_files) > 0:
        sys.exit(1)

    meta_file_path = (
        generate_queries_result.queries_to_generate.generated_code_path
        / STRICTQL_META_FILE_NAME
    )

    if not meta_file_path.exists():
        console.print(
            f"Meta file: {meta_file_path.resolve()} does not exist",
            style=Style(color="red", bold=True),
        )

    actual_meta_file_content = meta_file_path.read_text()
    expected_meta_file_content = generate_meta_file(
        path=generate_queries_result.queries_to_generate.generated_code_path,
        meta_file_name=STRICTQL_META_FILE_NAME,
        exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
    )

    if actual_meta_file_content != expected_meta_file_content:
        console.print(
            "Current meta file content not equals to expected content, looks like code was changed manually",
            style=Style(color="red", bold=True),
        )
        sys.exit(1)

    console.print(
        "Check completed successfully.", style=Style(color="green", bold=True)
    )


@app.command()  # type: ignore[misc] # Expression contains "Any", todo fix it on cyclopts
def init() -> None:
    """
    Init strictql config
    """
    if RESOLVED_PYPROJECT_TOML_PATH.exists():
        try:
            parsed_config = parse_toml_file_as_model(
                path=RESOLVED_PYPROJECT_TOML_PATH,
                model_type=ParsedPyprojectTomlWithStrictQLSection,
            )
        except Exception:
            pass
        else:
            console.print(
                f"StrictQL config already exists: {parsed_config.model_dump()}"  # type: ignore[misc] # model_dump contains Any
            )
            return

    code_generation_dir_path = questionary.path(  # type: ignore[misc] # signature contains Any
        "Path for the directory with the generated queries"
    ).ask()

    RESOLVED_PYPROJECT_TOML_PATH.touch(exist_ok=True)

    text = generate_strictql_section_to_pyproject_toml(
        databases={},
        code_generation_dir_path=code_generation_dir_path,  # type: ignore[misc]
    )
    current_content = RESOLVED_PYPROJECT_TOML_PATH.read_text()
    current_content += "\n" + text
    RESOLVED_PYPROJECT_TOML_PATH.write_text(current_content)

    console.print("StrictQL config generated", style=Style(color="green", bold=True))


if __name__ == "__main__":
    app()
