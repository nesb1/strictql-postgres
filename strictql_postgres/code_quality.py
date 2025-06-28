import asyncio
import pathlib
import sys

from strictql_postgres.format_exception import format_exception


class RuffCodeQualityError(Exception):
    pass


def decode_communication_result(
    communicate_result: tuple[bytes | None, bytes | None],
) -> tuple[str | None, str | None]:
    stdout = None if communicate_result[0] is None else communicate_result[0].decode()
    stderr = None if communicate_result[1] is None else communicate_result[1].decode()

    return stdout, stderr


async def run_ruff_lint_with_fix(code: str) -> str:
    subprocess = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "ruff",
        "check",
        "--extend-select",
        "I",
        "--fix-only",
        "-",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    communicate_result = await subprocess.communicate(input=code.encode())
    if subprocess.returncode is None:
        raise Exception("Subprocess return code is None, that is unexpected")
    if subprocess.returncode != 0:
        decoded_communicate_result = decode_communication_result(
            communicate_result=communicate_result
        )

        raise RuffCodeQualityError(
            f"Ruff linter failed with exit code {subprocess.returncode},"
            f" stdout: {decoded_communicate_result[0]} and stderr: {decoded_communicate_result[1]}"
        )

    return communicate_result[0].decode()


async def run_ruff_format(code: str) -> str:
    subprocess = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "ruff",
        "format",
        "-",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    communicate_result = await subprocess.communicate(input=code.encode())
    if subprocess.returncode is None:
        raise Exception("Subprocess return code is None, that is unexpected")
    if subprocess.returncode != 0:
        decoded_communicate_result = decode_communication_result(
            communicate_result=communicate_result
        )

        raise RuffCodeQualityError(
            f"Ruff format failed with exit code {subprocess.returncode},"
            f" stdout: {decoded_communicate_result[0]} and stderr: {decoded_communicate_result[1]}"
        )

    return communicate_result[0].decode()


class MypyCodeQualityError(Exception):
    pass


class MypyRunner:
    def __init__(self, mypy_path: pathlib.Path) -> None:
        """
        :param mypy_path: Required for correct work with local stubs for packages without typing annotations
        """
        self._mypy_path = mypy_path

    async def run_mypy(self, code: str) -> None:
        subprocess = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "mypy",
            "-c",
            code,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={"MYPYPATH": self._mypy_path},
        )

        communicate_result = await subprocess.communicate()
        if subprocess.returncode is None:
            raise Exception("Subprocess return code is None, that is unexpected")
        if subprocess.returncode != 0:
            decoded_communicate_result = decode_communication_result(
                communicate_result=communicate_result
            )

            raise MypyCodeQualityError(
                f"Mypy linter failed with exit code {subprocess.returncode},"
                f" stdout: {decoded_communicate_result[0]} and stderr: {decoded_communicate_result[1]}"
            )


class CodeQualityImproverError(Exception):
    pass


class CodeFixer:
    async def try_to_improve_code(self, code: str) -> str:
        try:
            code = await run_ruff_format(code=code)
            code = await run_ruff_lint_with_fix(code=code)
        except RuffCodeQualityError as error:
            raise CodeQualityImproverError(
                f"Code quality improvement failed: {format_exception(exception=error)}"
            ) from error

        return code
