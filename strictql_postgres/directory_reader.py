import pathlib
from typing import Mapping


def read_directory_python_files_recursive(
    path: pathlib.Path,
) -> Mapping[pathlib.Path, str]:
    res = {}
    for file in path.glob("**/*.py"):
        file_content = file.read_text(encoding="utf-8")

        res[file.resolve()] = file_content

    return res
