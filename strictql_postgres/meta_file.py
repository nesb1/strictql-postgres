import dataclasses
import hashlib
import pathlib

import pydantic


class MetaFileModel(pydantic.BaseModel):  # type: ignore[misc,explicit-any]
    files_checksums: dict[str, str]


@dataclasses.dataclass
class GenerateMetaFileError(Exception):
    error: str


def generate_meta_file(path: pathlib.Path, meta_file_name: str) -> MetaFileModel:
    if not path.exists():
        raise GenerateMetaFileError(f"Directory `{path}` not exists")
    if not path.is_dir():
        raise GenerateMetaFileError(f"`{path}` is not a directory")
    res = {}
    for item in path.rglob("*.py"):
        if item.is_dir() or item.is_file() and item.name == meta_file_name:
            continue
        res[str(item.relative_to(path))] = hashlib.sha256(item.read_bytes()).hexdigest()
    return MetaFileModel(files_checksums=res)
