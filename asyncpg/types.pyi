from typing import NamedTuple

class AttributeRowDescription(NamedTuple):
    name: str
    type: RowDescriptionType

class RowDescriptionType(NamedTuple):
    table_oid: int
    column_attribute_number: int
    oid: int
    name: str
    data_type_size: int
    type_modifier: int
    kind: str
    schema: str

class ParameterDescriptionType(NamedTuple):
    oid: int
    name: str
    kind: str
    schema: str
