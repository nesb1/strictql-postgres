def create_type_str(type_: type[object], is_optional: bool) -> str:
    raw_type = type_.__name__
    if is_optional:
        return f"{raw_type} | None"
    return raw_type
