import dataclasses


class StringNotInLowerSnakeCase(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class StringInSnakeLowerCase:
    value: str

    def __post_init__(self) -> None:
        if "_" in self.value:
            for snake_case_part in self.value.split("_"):
                if snake_case_part.lower() != snake_case_part:
                    raise StringNotInLowerSnakeCase(
                        "String contains upper case characters"
                    )
            return

        if self.value.lower() == self.value:
            return

        raise StringNotInLowerSnakeCase("String contains upper case characters")
