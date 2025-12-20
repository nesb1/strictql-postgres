import toml

from strictql_postgres.config_manager import (
    ParsedDatabase,
    ParsedPyprojectTomlWithStrictQLSection,
    ParsedStrictqlSettings,
    PyprojectTomlWithStrictQLToolSettings,
)


def generate_strictql_section_to_pyproject_toml(
    databases: dict[str, ParsedDatabase], code_generation_dir_path: str
) -> str:
    settings = ParsedStrictqlSettings(
        query_files_path=[],
        code_generate_dir=code_generation_dir_path,
        databases=databases,
    )

    data = ParsedPyprojectTomlWithStrictQLSection(
        tool=PyprojectTomlWithStrictQLToolSettings(strictql_postgres=settings)
    )

    return toml.dumps(data.model_dump())  # type: ignore[misc] # model_dump contains Any
