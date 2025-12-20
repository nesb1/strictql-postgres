python_versions := "3.11 3.12 3.13"

default:
    just --list

test:
    for python_version in {{ python_versions }}; do \
      uv run -p $python_version  python -m pytest -vv --cov strictql_postgres tests; \
    done

lint:
    for python_version in {{ python_versions }}; do \
      uv run -p $python_version --isolated  python -m ruff format --check strictql_postgres tests && uv run -p $python_version --isolated  python -m ruff check strictql_postgres tests --extend-select I && uv run -p $python_version --isolated  python -m mypy strictql_postgres tests;\
    done

fix:
    uv run  python -m ruff format strictql_postgres tests; \
    uv run  python -m ruff check --extend-select I --fix-only strictql_postgres tests; \

install:
    uv venv
    uv pip install -r pyproject.toml --group test --group lint
