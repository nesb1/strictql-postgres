import dataclasses
import pathlib
import shutil

from strictql_postgres.meta_file import (
    FILE_EXTENSIONS_TO_EXCLUDE,
    STRICTQL_META_FILE_NAME,
    generate_meta_file,
)
from strictql_postgres.python_types import FilesContentByPath


@dataclasses.dataclass
class GeneratedCodeWriterError(Exception):
    error: str

    def __str__(self) -> str:
        return self.error


def write_generated_code(
    target_directory: pathlib.Path, files: FilesContentByPath, meta_file_name: str
) -> None:
    if target_directory.exists():
        if not target_directory.is_dir():
            raise GeneratedCodeWriterError(
                error=f"Code generation path`{target_directory.resolve()}` is not a directory."
            )

        meta_file_content_path = target_directory / STRICTQL_META_FILE_NAME
        if not meta_file_content_path.exists():
            raise GeneratedCodeWriterError(
                error=f"Generated code directory: `{target_directory.resolve()}` already exists and does not contain a meta file {STRICTQL_META_FILE_NAME}."
                f" You probably specified the wrong directory or deleted the meta file. If you deleted the meta file yourself, then you need to manually delete the directory and regenerate the code."
            )
        meta_file_content = meta_file_content_path.read_text()
        expected_meta_file = generate_meta_file(
            path=target_directory,
            meta_file_name=meta_file_name,
            exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
        )
        if expected_meta_file != meta_file_content:
            raise GeneratedCodeWriterError(
                error=f"Generated code directory: `{target_directory.resolve()}` already exists and generated files in it are not equals to meta file content {STRICTQL_META_FILE_NAME}, looks like generated has been changed manually."
                f" Delete the generated code directory and regenerate the code."
            )

        shutil.rmtree(target_directory)

    target_directory.mkdir()

    for file_path, file_content in files.items():
        if file_path.parent != target_directory:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_content)
    meta_file_content = generate_meta_file(
        path=target_directory,
        meta_file_name=meta_file_name,
        exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
    )

    (target_directory / STRICTQL_META_FILE_NAME).write_text(meta_file_content)
