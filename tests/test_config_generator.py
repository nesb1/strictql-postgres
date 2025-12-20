from strictql_postgres.config_generator import (
    generate_strictql_section_to_pyproject_toml,
)
from strictql_postgres.config_manager import ParsedDatabase


def test_generate_pyproject_section() -> None:
    expected_text = """[tool.strictql_postgres]
query_files_path = []
code_generate_dir = "/kek/code_generation_dir"

[tool.strictql_postgres.databases.db1]
env_name_to_read_connection_url = "DB1"

[tool.strictql_postgres.databases.db2]
env_name_to_read_connection_url = "DB2"
"""

    actual_text = generate_strictql_section_to_pyproject_toml(
        databases={
            "db1": ParsedDatabase(env_name_to_read_connection_url="DB1"),
            "db2": ParsedDatabase(env_name_to_read_connection_url="DB2"),
        },
        code_generation_dir_path="/kek/code_generation_dir",
    )

    assert expected_text == actual_text
