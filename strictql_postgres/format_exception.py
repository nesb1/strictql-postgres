def format_exception(exception: BaseException) -> str:
    return f"{type(exception)}: {exception}"
