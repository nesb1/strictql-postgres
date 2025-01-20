class PostgresSyntaxError(Exception):
    message: str


class UndefinedTableError(Exception):
    message: str


class PostgresError(Exception):
    pass
