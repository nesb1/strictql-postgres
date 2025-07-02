import pathlib
import tempfile

import pytest

from strictql_postgres.generated_code_writer import (
    GeneratedCodeWriterError,
    write_generated_code,
)
from strictql_postgres.meta_file import (
    FILE_EXTENSIONS_TO_EXCLUDE,
    STRICTQL_META_FILE_NAME,
    generate_meta_file,
)


def test_write_generated_code_works_when_directory_does_not_exist() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        generated_code_directory = pathlib.Path(tmpdir) / "generated_code"

        assert not generated_code_directory.exists()

        files = {
            generated_code_directory / "file.py": "content",
            generated_code_directory / "subdir" / "file.py": "content",
        }
        write_generated_code(
            target_directory=generated_code_directory,
            files=files,
            meta_file_name=STRICTQL_META_FILE_NAME,
        )

        assert generated_code_directory.exists()

        for file_path, file_content in files.items():
            assert file_path.exists()
            assert file_path.read_text() == file_content

        meta_file = generated_code_directory / STRICTQL_META_FILE_NAME
        assert meta_file.exists()
        assert meta_file.read_text() == generate_meta_file(
            path=generated_code_directory,
            meta_file_name=STRICTQL_META_FILE_NAME,
            exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
        )


def test_write_generated_code_recreate_directory_when_directory_exists_and_meta_file_equals_to_content() -> (
    None
):
    with tempfile.TemporaryDirectory() as tmpdir:
        generated_code_directory = pathlib.Path(tmpdir) / "generated_code"
        assert not generated_code_directory.exists()

        old_file = {
            generated_code_directory / "file.py": "content",
            generated_code_directory / "subdir" / "file.py": "content",
        }
        write_generated_code(
            target_directory=generated_code_directory,
            files=old_file,
            meta_file_name=STRICTQL_META_FILE_NAME,
        )
        assert generated_code_directory.exists()

        for file_path, file_content in old_file.items():
            assert file_path.exists()
            assert file_path.read_text() == file_content

        meta_file = generated_code_directory / STRICTQL_META_FILE_NAME
        assert meta_file.exists()
        assert meta_file.read_text() == generate_meta_file(
            path=generated_code_directory,
            meta_file_name=STRICTQL_META_FILE_NAME,
            exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
        )

        new_files = {
            generated_code_directory / "new_file.py": "content",
        }

        write_generated_code(
            target_directory=generated_code_directory,
            files=new_files,
            meta_file_name=STRICTQL_META_FILE_NAME,
        )

        assert generated_code_directory.exists()

        for file_path, file_content in old_file.items():
            assert not file_path.exists()

        for file_path, file_content in new_files.items():
            assert file_path.exists()
            assert file_path.read_text() == file_content

        meta_file = generated_code_directory / STRICTQL_META_FILE_NAME
        assert meta_file.exists()
        assert meta_file.read_text() == generate_meta_file(
            path=generated_code_directory,
            meta_file_name=STRICTQL_META_FILE_NAME,
            exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
        )


def test_write_generated_code_raises_when_directory_exists_but_without_meta_file() -> (
    None
):
    with tempfile.TemporaryDirectory() as tmpdir:
        generated_code_directory = pathlib.Path(tmpdir) / "generated_code"

        assert not generated_code_directory.exists()

        generated_code_directory.mkdir()

        file = generated_code_directory / "file.py"
        file.write_text("text")

        files = {
            generated_code_directory / "another_file.py": "content",
            generated_code_directory / "subdir" / "file.py": "content",
        }

        with pytest.raises(GeneratedCodeWriterError) as error:
            write_generated_code(
                target_directory=generated_code_directory,
                files=files,
                meta_file_name=STRICTQL_META_FILE_NAME,
            )

        assert error.value.error == (
            f"Generated code directory: `{generated_code_directory.resolve()}` already exists and does not contain a meta file {STRICTQL_META_FILE_NAME}."
            f" You probably specified the wrong directory or deleted the meta file. If you deleted the meta file yourself, then you need to manually delete the directory and regenerate the code."
        )
        assert file.exists()

        for file_path, file_content in files.items():
            assert not file_path.exists()


def test_write_generated_code_raises_when_directory_exists_but_another_meta_file() -> (
    None
):
    with tempfile.TemporaryDirectory() as tmpdir:
        generated_code_directory = pathlib.Path(tmpdir) / "generated_code"

        assert not generated_code_directory.exists()

        generated_code_directory.mkdir()

        file = generated_code_directory / "file.py"
        file.write_text("text")
        (generated_code_directory / STRICTQL_META_FILE_NAME).write_text(
            "invalid meta file text"
        )

        files = {
            generated_code_directory / "another_file.py": "content",
            generated_code_directory / "subdir" / "file.py": "content",
        }

        with pytest.raises(GeneratedCodeWriterError) as error:
            write_generated_code(
                target_directory=generated_code_directory,
                files=files,
                meta_file_name=STRICTQL_META_FILE_NAME,
            )

        assert error.value.error == (
            f"Generated code directory: `{generated_code_directory.resolve()}` already exists and generated files in it are not equals to meta file content {STRICTQL_META_FILE_NAME}, looks like generated has been changed manually."
            f" Delete the generated code directory and regenerate the code."
        )
        assert file.exists()

        for file_path, file_content in files.items():
            assert not file_path.exists()


def test_write_generated_code_raises_when_directory_is_not_a_directory() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = pathlib.Path(tmpdir)
        file = directory / "file.py"
        file.write_text("text")
        with pytest.raises(GeneratedCodeWriterError) as error:
            write_generated_code(
                target_directory=file,
                files={},
                meta_file_name=STRICTQL_META_FILE_NAME,
            )

            assert (
                error.value.error
                == f"Code generation path`{file.resolve()}` is not a directory."
            )
