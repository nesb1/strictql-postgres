python_versions := "3.11 3.12 3.13"

default:
    just --list

test:
    for python_version in {{ python_versions }}; do \
      uv run -p $python_version --isolated  python -m pytest -vv --cov strictql_postgres tests; \
    done

lint:
    for python_version in {{ python_versions }}; do \
      uv run -p $python_version --isolated  python -m ruff format --check strictql_postgres tests && uv run -p $python_version --isolated  python -m ruff check strictql_postgres tests && uv run -p $python_version --isolated  python -m mypy strictql_postgres tests;\
    done

fix:
    uv run --isolated  python -m ruff format strictql_postgres tests; \
    uv run --isolated  python -m ruff check --fix-only strictql_postgres tests; \

install:
    uv venv
    uv export --format requirements-txt --group test | uv pip install -r - -p 3.13 # uv export because https://github.com/astral-sh/uv/issues/8590
