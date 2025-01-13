python_versions := "3.11 3.12 3.13"

test:
    for python_version in {{ python_versions }}; do \
      uv run -p $python_version --with="pydantic>=2" --isolated  python -m pytest --cov strictql_postgres tests; \
      uv run -p $python_version --with="pydantic<2" --isolated  python -m pytest --cov strictql_postgres tests; \
    done

install:
    uv venv
    uv export --format requirements-txt --only-group test | uv pip install -r - -p 3.13 # export because https://github.com/astral-sh/uv/issues/8590
