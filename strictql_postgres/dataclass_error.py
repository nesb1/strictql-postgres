import dataclasses


@dataclasses.dataclass(frozen=True)
class Error(Exception):
    error: str

    def __str__(self) -> str:
        return self.error
