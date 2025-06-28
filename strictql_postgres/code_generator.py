import dataclasses

from mako.template import (  # type: ignore[import-untyped] # mako has not typing annotations
    Template,
)

from pglast import prettify
from strictql_postgres.code_quality import (
    CodeFixer,
    CodeQualityImproverError,
)
from strictql_postgres.common_types import BindParams, NotEmptyRowSchema
from strictql_postgres.format_exception import format_exception
from strictql_postgres.model_name_generator import generate_model_name_by_function_name
from strictql_postgres.python_types import (
    InnerModelType,
    ModelType,
    format_type,
)
from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase
from strictql_postgres.templates import TEMPLATES_DIR


class GenerateCodeError(Exception):
    pass


@dataclasses.dataclass
class BindParamToTemplate:
    name_in_function: str
    type_str: str


async def generate_code_for_query_with_fetch_row_method(
    query: str,
    result_schema: NotEmptyRowSchema,
    bind_params: BindParams,
    function_name: StringInSnakeLowerCase,
    code_quality_improver: CodeFixer,
) -> str:
    query = prettify(query)
    model_type = ModelType(
        name=generate_model_name_by_function_name(function_name=function_name),
        fields=result_schema.schema,
    )

    formatted_type = format_type(
        type=InnerModelType(model_type=model_type, is_optional=False),
    )
    imports = {
        "from asyncpg import Connection",
        "from datetime import timedelta",
        "from strictql_postgres.api import convert_record_to_pydantic_model",
    }
    imports |= formatted_type.imports
    rendered_code: str
    if len(bind_params) == 0:
        mako_template_path = (
            TEMPLATES_DIR / "fetch_row_without_params.txt"
        ).read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            imports=imports,
            model_name=formatted_type.type_,
            function_name=function_name.value,
            models=formatted_type.models_code,
            query=query,
            params=[],
        )
    else:
        mako_template_path = (TEMPLATES_DIR / "fetch_row_with_params.txt").read_text()
        formatted_bind_params = []
        models = formatted_type.models_code
        for bind_param in bind_params:
            formatted_type = format_type(bind_param.type_)
            models |= formatted_type.models_code
            imports |= formatted_type.imports
            formatted_bind_params.append(
                BindParamToTemplate(
                    name_in_function=bind_param.name_in_function,
                    type_str=formatted_type.type_,
                )
            )
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            imports=imports,
            models=models,
            function_name=function_name.value,
            model_name=model_type.name,
            query=query,
            params=formatted_bind_params,
        )

    try:
        return await code_quality_improver.try_to_improve_code(code=rendered_code)
    except CodeQualityImproverError as code_quality_improver_error:
        raise GenerateCodeError(
            f"Code quality improver failed: {format_exception(exception=code_quality_improver_error)}"
        ) from code_quality_improver_error


async def generate_code_for_query_with_fetch_all_method(
    query: str,
    result_schema: NotEmptyRowSchema,
    bind_params: BindParams,
    function_name: StringInSnakeLowerCase,
    code_quality_improver: CodeFixer,
) -> str:
    query = prettify(query)
    model_type = ModelType(
        name=generate_model_name_by_function_name(function_name=function_name),
        fields=result_schema.schema,
    )

    formatted_type = format_type(
        type=InnerModelType(model_type=model_type, is_optional=False),
    )
    imports = {
        "from asyncpg import Connection",
        "from datetime import timedelta",
        "from collections.abc import Sequence",
        "from strictql_postgres.api import convert_records_to_pydantic_models",
    }
    imports |= formatted_type.imports
    rendered_code: str
    if len(bind_params) == 0:
        mako_template_path = (
            TEMPLATES_DIR / "fetch_all_without_params.txt"
        ).read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            imports=imports,
            model_name=formatted_type.type_,
            function_name=function_name.value,
            models=formatted_type.models_code,
            query=query,
            params=[],
        )
    else:
        mako_template_path = (TEMPLATES_DIR / "fetch_all_with_params.txt").read_text()
        formatted_bind_params = []
        models = formatted_type.models_code
        for bind_param in bind_params:
            formatted_type = format_type(bind_param.type_)
            models |= formatted_type.models_code
            imports |= formatted_type.imports
            formatted_bind_params.append(
                BindParamToTemplate(
                    name_in_function=bind_param.name_in_function,
                    type_str=formatted_type.type_,
                )
            )
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            imports=imports,
            models=models,
            function_name=function_name.value,
            model_name=model_type.name,
            query=query,
            params=formatted_bind_params,
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
    code_quality_improver: CodeFixer,
) -> str:
    query = prettify(query)
    rendered_code: str
    imports = {
        "from asyncpg import Connection",
        "from datetime import timedelta",
    }
    if len(bind_params) == 0:
        mako_template_path = (TEMPLATES_DIR / "execute_without_params.txt").read_text()
        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            function_name=function_name.value,
            imports=imports,
            query=query,
            params=[],
        )
    else:
        mako_template_path = (TEMPLATES_DIR / "execute_with_params.txt").read_text()

        formatted_bind_params = []
        models = set()
        for bind_param in bind_params:
            formatted_type = format_type(bind_param.type_)
            models |= formatted_type.models_code
            imports |= formatted_type.imports
            formatted_bind_params.append(
                BindParamToTemplate(
                    name_in_function=bind_param.name_in_function,
                    type_str=formatted_type.type_,
                )
            )

        rendered_code = Template(mako_template_path).render(  # type: ignore[misc] # Any expression because mako has not typing annotations
            function_name=function_name.value,
            query=query,
            params=formatted_bind_params,
            imports=imports,
            models=models,
        )

    try:
        return await code_quality_improver.try_to_improve_code(code=rendered_code)
    except CodeQualityImproverError as code_quality_improver_error:
        raise GenerateCodeError(
            f"Code quality improver failed: {format_exception(exception=code_quality_improver_error)}"
        ) from code_quality_improver_error
