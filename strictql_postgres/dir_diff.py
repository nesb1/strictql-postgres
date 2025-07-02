import difflib
import pathlib

from strictql_postgres.python_types import FilesContentByPath

Diff = str


def get_missed_files(
    actual: FilesContentByPath, expected: FilesContentByPath
) -> set[pathlib.Path]:
    missed = set()
    for path in expected.keys():
        if path not in actual:
            missed.add(path)

    return missed


def get_diff_for_changed_files(
    actual: FilesContentByPath, expected: FilesContentByPath
) -> dict[pathlib.Path, Diff]:
    changed_files_diff = {}
    for file_path, actual_file_content in actual.items():
        if file_path not in expected:
            continue

        expected_file_content = expected[file_path]

        file_diff = "\n".join(
            difflib.unified_diff(
                expected_file_content.splitlines(),
                actual_file_content.splitlines(),
            )
        )
        if file_diff:
            changed_files_diff[file_path] = file_diff

    return changed_files_diff
