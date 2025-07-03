import pathlib
import tempfile

from strictql_postgres.directory_reader import read_directory_python_files_recursive


def test_read_directory_python_files_recursive() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(tmpdir).resolve()

        inner_dir = path / "inner_dir"
        inner_dir.mkdir()
        inner_dir_file = inner_dir / "file.py"
        inner_dir_file.write_text("some text")
        inner_inner_dir = inner_dir / "inner_dir"
        inner_inner_dir.mkdir()
        inner_inner_dir_file = inner_inner_dir / "file.py"
        inner_inner_dir_file.write_text("some text 1231")
        file = path / "file.py"
        file.write_text("some text 321")

        expected = {
            file: "some text 321",
            inner_dir_file: "some text",
            inner_inner_dir_file: "some text 1231",
        }

        assert read_directory_python_files_recursive(path) == expected
