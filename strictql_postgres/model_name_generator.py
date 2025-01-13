from strictql_postgres.string_in_snake_case import StringInSnakeLowerCase


def generate_model_name_by_function_name(function_name: StringInSnakeLowerCase) -> str:
    function_name_in_camel_case = "".join(
        [
            snake_case_part.lower().capitalize()
            for snake_case_part in function_name.value.split("_")
        ]
    )
    return f"{function_name_in_camel_case}Model"
