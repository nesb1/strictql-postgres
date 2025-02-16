from asyncpg.types import Type, Attribute

class PreparedStatement:
    """A representation of a prepared statement."""

    def get_parameters(self) -> tuple[Type, ...]: ...
    def get_attributes(self) -> tuple[Attribute, ...]: ...
