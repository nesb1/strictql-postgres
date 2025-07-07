import dataclasses
import hashlib
import os
import pathlib

import pydantic


class MetaFileModel(pydantic.BaseModel):  # type: ignore[explicit-any]
    files_checksums: dict[str, str]


@dataclasses.dataclass
class GenerateMetaFileError(Exception):
    error: str


STRICTQL_META_FILE_NAME = "strictql_meta"

FILE_EXTENSIONS_TO_EXCLUDE = {".pyc"}


def generate_meta_file(
    path: pathlib.Path, meta_file_name: str, exclude_file_extensions: set[str]
) -> str:
    if not path.exists():
        raise GenerateMetaFileError(f"Directory `{path}` not exists")
    if not path.is_dir():
        raise GenerateMetaFileError(f"`{path}` is not a directory")
    res = {}
    for item in path.rglob("*"):
        if item.is_dir() or item.is_file() and item.name == meta_file_name:
            continue

        file_extension = os.path.splitext(item.name)[1]
        if item.is_file() and file_extension in exclude_file_extensions:
            continue

        res[str(item.relative_to(path))] = hashlib.sha256(item.read_bytes()).hexdigest()
    return hashlib.sha256(
        MetaFileModel(files_checksums=res).model_dump_json().encode("utf-8")
    ).hexdigest()
