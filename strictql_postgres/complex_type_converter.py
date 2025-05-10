import pydantic
from pydantic.fields import FieldInfo


def convert_postgres_complex_type_to_bind_param_value(
    complex_type: pydantic.BaseModel,
) -> tuple[object, ...]:
    field_info: FieldInfo
    values: list[object] = []
    for field_name, field_info in complex_type.model_fields.items():
        field_value: object = getattr(complex_type, field_name)

        if isinstance(field_value, pydantic.BaseModel):  # type: ignore[misc]
            values.append(
                convert_postgres_complex_type_to_bind_param_value(field_value)
            )
        elif isinstance(field_value, list):
            list_values = []
            for value in field_value:
                if isinstance(value, pydantic.BaseModel):  # type: ignore[misc]
                    list_values.append(
                        convert_postgres_complex_type_to_bind_param_value(value)
                    )
                else:
                    list_values.append(value)

            values.append(tuple(list_values))
        else:
            values.append(field_value)

    return tuple(values)
