def create_type_str(type_: str, is_optional: bool) -> str:
    if is_optional:
        return f"{type_} | None"
    return type_
