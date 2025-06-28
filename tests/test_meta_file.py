import pathlib
import tempfile

import pytest

from strictql_postgres.meta_file import (
    GenerateMetaFileError,
    MetaFileModel,
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

        assert generate_meta_file(tmp_dir_path, meta_file_name="") == MetaFileModel(
            files_checksums={
                "file1.py": "7aaac2a16de6c1e9b340dd1763d95246ba8103318aa040adf6767cb6040b769d",
                "subdir/file2.py": "548fdebb828e73402772d16dd825c9e6b1dac0e1a15d60a79c73140086161995",
            }
        )


def test_generate_meta_file_raises_error_when_directory_does_not_exists() -> None:
    with pytest.raises(GenerateMetaFileError) as error:
        path = pathlib.Path("nonexistent").resolve()
        generate_meta_file(path=path, meta_file_name="")

    assert error.value.error == f"Directory `{path}` not exists"


def test_generate_meta_file_raises_error_when_path_is_not_a_directory() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(tmpdir).resolve()
        file = path / "file.py"
        file.touch()
        with pytest.raises(GenerateMetaFileError) as error:
            generate_meta_file(path=file, meta_file_name="")

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

        assert generate_meta_file(tmp_dir_path, meta_file.name) == MetaFileModel(
            files_checksums={
                "file1.py": "7aaac2a16de6c1e9b340dd1763d95246ba8103318aa040adf6767cb6040b769d",
                "subdir/file2.py": "548fdebb828e73402772d16dd825c9e6b1dac0e1a15d60a79c73140086161995",
            }
        )
