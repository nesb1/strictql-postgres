import dataclasses
from typing import Literal

from strictql_postgres.code_quality import (
    CodeQualityImprover,
    CodeQualityImproverError,
)
from mako.template import Template  # type: ignore[import-untyped] # mako has not typing annotations

from strictql_postgres.format_exception import format_exception
from strictql_postgres.templates import TEMPLATES_DIR

ColumnName = str
ColumnType = type[object]

DataBaseRowModel = dict[ColumnName, ColumnType]


@dataclasses.dataclass
class QueryWithDBInfo:
    query: str
    query_result_row_model: DataBaseRowModel


@dataclasses.dataclass
class StrictQLGeneratedCode:
    imports: str
    model_definition: str
    function_definition: str


class GenerateCodeError(Exception):
    pass


async def generate_code_for_query(
    query_with_db_info: QueryWithDBInfo,
    execution_variant: Literal["fetch_all"],
    function_name: str,
    code_quality_improver: CodeQualityImprover,
) -> str:
    fields = {
        field_name: field_type.__name__
        for field_name, field_type in query_with_db_info.query_result_row_model.items()
    }
    model_name = "Model"
    mako_template_path = (TEMPLATES_DIR / "mako_template.txt").read_text()
    rendered_code: str = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
        model_name=model_name,
        fields=fields.items(),
        function_name=function_name,
        query=query_with_db_info.query,
    )

    try:
        return await code_quality_improver.try_to_improve_code(code=rendered_code)
    except CodeQualityImproverError as code_quality_improver_error:
        raise GenerateCodeError(
            f"Code quality improver failed: {format_exception(exception=code_quality_improver_error)}"
        ) from code_quality_improver_error
