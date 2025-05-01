from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Literal, Mapping, Union

from mako.template import (  # type: ignore[import-untyped] # mako has not typing annotations
    Template,
)

from strictql_postgres.templates import TEMPLATES_DIR
from strictql_postgres.type_str_creator import create_type_str


class SimpleTypes(enum.Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    BYTES = "bytes"


ALL_TYPES = Union["ListType", "SimpleType", "InnerModelType", "TypesWithImport"]


@dataclass
class SimpleType:
    type_: SimpleTypes
    is_optional: bool


@dataclass
class ListType:
    generic_type: ALL_TYPES
    is_optional: bool


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


@dataclass
class ClassType:
    fields: dict[str, ALL_TYPES]


INT_TYPE = SimpleType(type_=SimpleTypes.INT, is_optional=True)
LIST_OF_INTS = ListType(INT_TYPE, is_optional=True)


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


@dataclass()
class GeneratedCodeWithModelDefinitions:
    imports: set[str]
    models_code: set[str]


def format_simple_type(type_: SimpleType) -> str:
    if not type_.is_optional:
        return type_.type_.value
    return f"{type_.type_.value} | None"


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
        elif isinstance(type_, SimpleType):
            fields[name] = create_type_str(
                type_=type_.type_.value, is_optional=type_.is_optional
            )
        elif isinstance(type_, InnerModelType):
            generated_code = generate_code_for_model_as_pydantic(
                model_type=type_.model_type
            )
            imports.update(generated_code.imports)
            models.update(generated_code.models_code)
            fields[name] = create_type_str(
                type_=type_.model_type.name, is_optional=type_.is_optional
            )

    mako_template = (TEMPLATES_DIR / "pydantic_model.txt").read_text()
    model_code = (
        Template(mako_template)  # type: ignore [misc]
        .render(fields=fields, model_name=model_type.name)
        .strip()
    )
    models.add(model_code)  # type: ignore [misc]

    return GeneratedCodeWithModelDefinitions(imports=imports, models_code=models)
