import dataclasses
import pathlib

import tomllib


class TomlParserError(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class TomlNotFoundError(TomlParserError):
    path: pathlib.Path


@dataclasses.dataclass(frozen=True)
class TomlNotValidTomlError(TomlParserError):
    error: str


def parse_toml_file(path: pathlib.Path) -> dict[str, object]:
    if not path.exists():
        raise TomlNotFoundError(path=path)
    content = path.read_text()
    try:
        return tomllib.loads(content)  # type: ignore[misc]
    except tomllib.TOMLDecodeError as error:
        raise TomlNotValidTomlError(error=str(error)) from error
