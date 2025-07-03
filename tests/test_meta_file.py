import pathlib
import tempfile

import pytest

from strictql_postgres.meta_file import (
    FILE_EXTENSIONS_TO_EXCLUDE,
    STRICTQL_META_FILE_NAME,
    GenerateMetaFileError,
    generate_meta_file,
)


def test_generate_meta_file_works() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = pathlib.Path(tmpdir)
        file1 = tmp_dir_path / "file1.py"
        sub_dir = tmp_dir_path / "subdir"
        sub_dir.mkdir()
        file2 = sub_dir / "file2.py"

        file1.write_text("som text 1231231")
        file2.write_text("som text 32131231")

        assert (
            generate_meta_file(
                tmp_dir_path,
                meta_file_name="",
                exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
            )
            == "f877da1a11d2f763fedcf6531a0cbec50a8ce4244d412026d3ee155f9df03ddf"
        )


def test_generate_meta_file_raises_error_when_directory_does_not_exists() -> None:
    with pytest.raises(GenerateMetaFileError) as error:
        path = pathlib.Path("nonexistent").resolve()
        generate_meta_file(
            path=path,
            meta_file_name="",
            exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
        )

    assert error.value.error == f"Directory `{path}` not exists"


def test_generate_meta_file_raises_error_when_path_is_not_a_directory() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(tmpdir).resolve()
        file = path / "file.py"
        file.touch()
        with pytest.raises(GenerateMetaFileError) as error:
            generate_meta_file(
                path=file,
                meta_file_name="",
                exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
            )

    assert error.value.error == f"`{file}` is not a directory"


def test_generate_meta_file_skip_meta_file() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = pathlib.Path(tmpdir)
        file1 = tmp_dir_path / "file1.py"
        sub_dir = tmp_dir_path / "subdir"
        sub_dir.mkdir()
        file2 = sub_dir / "file2.py"

        file1.write_text("som text 1231231")
        file2.write_text("som text 32131231")

        meta_file = tmp_dir_path / "meta_file"
        meta_file.write_text("some meta file text")

        assert (
            generate_meta_file(
                tmp_dir_path,
                meta_file.name,
                exclude_file_extensions=FILE_EXTENSIONS_TO_EXCLUDE,
            )
            == "f877da1a11d2f763fedcf6531a0cbec50a8ce4244d412026d3ee155f9df03ddf"
        )


def test_generate_meta_file_skip_excluded_extensions() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir_path = pathlib.Path(tmpdir)
        file = tmp_dir_path / "file.py"
        file.write_text("som text 1231231")

        meta_file_content_before_file_with_extension_to_skip = generate_meta_file(
            tmp_dir_path,
            meta_file_name=STRICTQL_META_FILE_NAME,
            exclude_file_extensions={"txt"},
        )

        file_with_extension_to_skip = tmp_dir_path / "file_with_extensions_to_skip.txt"
        file_with_extension_to_skip.write_text("text")

        meta_file_content_after_file_with_extension_to_skip = generate_meta_file(
            tmp_dir_path,
            meta_file_name=STRICTQL_META_FILE_NAME,
            exclude_file_extensions={".txt"},
        )

        assert (
            meta_file_content_before_file_with_extension_to_skip
            == meta_file_content_after_file_with_extension_to_skip
        )
