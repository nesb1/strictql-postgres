import os
import pathlib
import tempfile

import pytest

from strictql_postgres.code_quality import (
    run_ruff_lint_with_fix,
    RuffCodeQualityError,
    MypyCodeQualityError,
    run_ruff_format,
    MypyRunner,
)
from tests.conftest import PROJECT_ROOT


async def test_ruff_check_with_fix_works() -> None:
    code = 'f"123"'
    fixed_code = await run_ruff_lint_with_fix(code=code)
    assert fixed_code == '"123"'


async def test_ruff_check_with_fix_works_when_no_fix_required() -> None:
    code = "a = 1"
    fixed_code = await run_ruff_lint_with_fix(code=code)
    assert fixed_code == "a = 1"


async def test_ruff_check_error() -> None:
    code_with_ruff_error = "True == True"
    with pytest.raises(RuffCodeQualityError):
        await run_ruff_lint_with_fix(code=code_with_ruff_error)


async def test_ruff_format() -> None:
    code = "a=1"
    fixed_code = await run_ruff_format(code=code)
    assert fixed_code == "a = 1\n"


async def test_ruff_format_error() -> None:
    code_with_ruff_error = "syntax error"
    with pytest.raises(RuffCodeQualityError):
        await run_ruff_lint_with_fix(code=code_with_ruff_error)


def test_project_root_is_actual() -> None:
    directories_at_project_root = [
        directory.name for directory in PROJECT_ROOT.iterdir()
    ]
    assert "tests" in directories_at_project_root
    assert "strictql_postgres" in directories_at_project_root


async def test_run_mypy_when_no_error() -> None:
    runner = MypyRunner(mypy_path=PROJECT_ROOT)
    code = "a: int = 1"

    await runner.run_mypy(code=code)


async def test_run_mypy_when_not_correct_mypy_path_provided_for_stubs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        current_working_directory = os.getcwd()
        # change current directory to catch mypy fail on pytest run from project root
        # else mypy will use stubs despite on invalid `mypy_path` argument.
        os.chdir(tmpdir)
        try:
            runner = MypyRunner(mypy_path=pathlib.Path(tmpdir))
            code = "import asyncpg"
            with pytest.raises(MypyCodeQualityError):
                await runner.run_mypy(code=code)
        finally:
            os.chdir(current_working_directory)


async def test_run_mypy_when_correct_mypy_path_provided_for_stubs() -> None:
    runner = MypyRunner(mypy_path=PROJECT_ROOT)
    code = "import asyncpg"
    await runner.run_mypy(code=code)


async def test_run_mypy_when_error() -> None:
    runner = MypyRunner(mypy_path=PROJECT_ROOT)
    code = 'a: int ="b"'

    with pytest.raises(MypyCodeQualityError):
        await runner.run_mypy(code=code)
