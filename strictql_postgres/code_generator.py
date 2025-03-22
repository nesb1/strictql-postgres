import dataclasses

from mako.template import Template  # type: ignore[import-untyped] # mako has not typing annotations

from strictql_postgres.code_quality import (
    CodeQualityImprover,
    CodeQualityImproverError,
)
from strictql_postgres.common_types import NotEmptyRowSchema, BindParams
from strictql_postgres.format_exception import format_exception
from strictql_postgres.model_name_generator import generate_model_name_by_function_name
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.templates import TEMPLATES_DIR
from strictql_postgres.type_str_creator import create_type_str


class GenerateCodeError(Exception):
    pass


@dataclasses.dataclass
class BindParamToTemplate:
    name_in_function: str
    type_str: str


async def generate_code_for_query_with_fetch_all_method(
    query: str,
    result_schema: NotEmptyRowSchema,
    bind_params: BindParams,
    function_name: StringInSnakeLowerCase,
    code_quality_improver: CodeQualityImprover,
) -> str:
    fields = {
        field_name: (
            f"{field_type.type_.__name__} | None"
            if field_type.is_optional
            else f"{field_type.type_.__name__}"
        )
        for field_name, field_type in result_schema.schema.items()
    }

    model_name = generate_model_name_by_function_name(function_name=function_name)
    rendered_code: str
    if len(bind_params) == 0:
        mako_template_path = (
            TEMPLATES_DIR / "fetch_all_without_params.txt"
        ).read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            model_name=model_name,
            fields=fields.items(),
            function_name=function_name.value,
            query=query,
            params=[],
        )
    else:
        mako_template_path = (TEMPLATES_DIR / "fetch_all_with_params.txt").read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            model_name=model_name,
            fields=fields.items(),
            function_name=function_name.value,
            query=query,
            params=[
                BindParamToTemplate(
                    name_in_function=bind_param.name_in_function,
                    type_str=create_type_str(
                        type_=bind_param.type_, is_optional=bind_param.is_optional
                    ),
                )
                for bind_param in bind_params
            ],
        )

    try:
        return await code_quality_improver.try_to_improve_code(code=rendered_code)
    except CodeQualityImproverError as code_quality_improver_error:
        raise GenerateCodeError(
            f"Code quality improver failed: {format_exception(exception=code_quality_improver_error)}"
        ) from code_quality_improver_error


async def generate_code_for_query_with_execute_method(
    query: str,
    bind_params: BindParams,
    function_name: StringInSnakeLowerCase,
    code_quality_improver: CodeQualityImprover,
) -> str:
    rendered_code: str
    if len(bind_params) == 0:
        mako_template_path = (TEMPLATES_DIR / "execute_without_params.txt").read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            function_name=function_name.value,
            query=query,
            params=[],
        )
    else:
        mako_template_path = (TEMPLATES_DIR / "execute_with_params.txt").read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            function_name=function_name.value,
            query=query,
            params=[
                BindParamToTemplate(
                    name_in_function=bind_param.name_in_function,
                    type_str=create_type_str(
                        type_=bind_param.type_, is_optional=bind_param.is_optional
                    ),
                )
                for bind_param in bind_params
            ],
        )

    try:
        return await code_quality_improver.try_to_improve_code(code=rendered_code)
    except CodeQualityImproverError as code_quality_improver_error:
        raise GenerateCodeError(
            f"Code quality improver failed: {format_exception(exception=code_quality_improver_error)}"
        ) from code_quality_improver_error
