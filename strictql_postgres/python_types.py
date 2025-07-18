from __future__ import annotations

import dataclasses
import pathlib
import typing
from dataclasses import dataclass
from typing import Literal, Mapping, Union

from mako.template import (  # type: ignore[import-untyped] # mako has not typing annotations
    Template,
)

from strictql_postgres.templates import TEMPLATES_DIR
from strictql_postgres.type_str_creator import create_type_str

ALL_TYPES = Union[
    "SimpleTypes",
    "InnerModelType",
    "TypesWithImport",
    "RecursiveListType",
]


@dataclasses.dataclass()
class Bool:
    is_optional: bool


@dataclasses.dataclass()
class String:
    is_optional: bool


@dataclasses.dataclass()
class Integer:
    is_optional: bool


@dataclasses.dataclass()
class Float:
    is_optional: bool


@dataclasses.dataclass()
class Bytes:
    is_optional: bool


@dataclasses.dataclass()
class Json:
    is_optional: bool


SimpleTypes = Bool | String | Integer | Float | Bool | Bytes | Json


@dataclass
class DecimalType:
    is_optional: bool
    name: Literal["Decimal"] = "Decimal"
    from_: Literal["decimal"] = "decimal"


@dataclass
class DateType:
    is_optional: bool
    name: Literal["date"] = "date"
    from_: Literal["datetime"] = "datetime"


@dataclass
class DateTimeType:
    is_optional: bool
    name: Literal["datetime"] = "datetime"
    from_: Literal["datetime"] = "datetime"


@dataclass
class TimeType:
    is_optional: bool
    name: Literal["time"] = "time"
    from_: Literal["datetime"] = "datetime"


@dataclass
class TimeDeltaType:
    is_optional: bool
    name: Literal["timedelta"] = "timedelta"
    from_: Literal["datetime"] = "datetime"


@dataclass
class ModelType:
    name: str
    fields: Mapping[str, ALL_TYPES]


@dataclass
class InnerModelType:
    model_type: ModelType
    is_optional: bool


TypesWithImport = DecimalType | DateTimeType | DateType | TimeType | TimeDeltaType


RecursiveListSupportedTypes = Union[SimpleTypes, TypesWithImport]


@dataclass(frozen=True)
class Import:
    from_: str
    name: str

    def format(self) -> str:
        return f"from {self.from_} import {self.name}"


@dataclass(frozen=True)
class FormattedTypeWithImport:
    type_as_str: str
    import_as_str: str


@dataclass(frozen=True)
class GeneratedCodeWithModelDefinitions:
    imports: set[str]
    main_model_name: str
    models_code: set[str]


@dataclass(frozen=True)
class FormattedType:
    imports: set[str]
    models_code: set[str]
    type_: str


def format_simple_type(type_: SimpleTypes) -> str:
    match type_:
        case String():
            type_name = "str"
        case Integer():
            type_name = "int"
        case Float():
            type_name = "float"
        case Bytes():
            type_name = "bytes"
        case Bool():
            type_name = "bool"
        case Json():
            type_name = "str"
        case _:
            typing.assert_never(type_)
    if not type_.is_optional or type_name == "object":
        return type_name
    return f"{type_name} | None"


def format_type_with_import(type_: TypesWithImport) -> FormattedTypeWithImport:
    return FormattedTypeWithImport(
        type_as_str=type_.name if not type_.is_optional else f"{type_.name} | None",
        import_as_str=f"from {type_.from_} import {type_.name}",
    )


def generate_code_for_model_as_pydantic(
    model_type: ModelType,
) -> GeneratedCodeWithModelDefinitions:
    imports = {Import(from_="pydantic", name="BaseModel").format()}
    fields = {}
    models: set[str] = set()
    for name, type_ in model_type.fields.items():
        if isinstance(type_, TypesWithImport):
            imports.add(Import(from_=type_.from_, name=type_.name).format())
            fields[name] = create_type_str(
                type_=type_.name, is_optional=type_.is_optional
            )
        elif isinstance(type_, SimpleTypes):
            fields[name] = format_simple_type(type_=type_)
        elif isinstance(type_, InnerModelType):
            generated_code = generate_code_for_model_as_pydantic(
                model_type=type_.model_type
            )
            imports.update(generated_code.imports)
            models.update(generated_code.models_code)
            fields[name] = create_type_str(
                type_=type_.model_type.name, is_optional=type_.is_optional
            )
        elif isinstance(type_, RecursiveListType):
            recursive_list_code = generate_recursive_list_definition(type_)
            imports.update(recursive_list_code.imports)
            models.update(recursive_list_code.models_code)
            fields[name] = recursive_list_code.type_
        else:
            raise NotImplementedError(type_)

    mako_template = (TEMPLATES_DIR / "pydantic_model.txt").read_text()
    model_code = (
        Template(mako_template)  # type: ignore [misc]
        .render(fields=fields, model_name=model_type.name)
        .strip()
    )
    models.add(model_code)  # type: ignore [misc]

    return GeneratedCodeWithModelDefinitions(
        imports=imports,
        models_code=models,
        main_model_name=model_type.name,
    )


def format_type(type: ALL_TYPES) -> FormattedType:
    if isinstance(type, SimpleTypes):
        return FormattedType(
            imports=set(),
            models_code=set(),
            type_=format_simple_type(type_=type),
        )
    if isinstance(type, TypesWithImport):
        return FormattedType(
            imports={f"from {type.from_} import {type.name}"},
            models_code=set(),
            type_=create_type_str(type_=type.name, is_optional=type.is_optional),
        )
    if isinstance(type, InnerModelType):
        generated_code = generate_code_for_model_as_pydantic(model_type=type.model_type)
        return FormattedType(
            imports=generated_code.imports,
            models_code=generated_code.models_code,
            type_=type.model_type.name,
        )
    if isinstance(type, RecursiveListType):
        return generate_recursive_list_definition(t=type)
    raise NotImplementedError(type)


FilesContentByPath = Mapping[pathlib.Path, str]


@dataclasses.dataclass
class RecursiveListType:
    generic_type: RecursiveListSupportedTypes
    is_optional: bool


def generate_recursive_list_definition(t: RecursiveListType) -> FormattedType:
    formatted_inner_type = format_type(t.generic_type)

    type_name = f"list[{formatted_inner_type.type_} | list[{formatted_inner_type.type_} | list[{formatted_inner_type.type_} | object]]]"

    if t.is_optional:
        type_name += " | None"
    return FormattedType(
        imports={
            *formatted_inner_type.imports,
            "from typing import TypeAliasType",
            "from typing import Union",
        },
        models_code={
            *formatted_inner_type.models_code,
        },
        type_=type_name,
    )
