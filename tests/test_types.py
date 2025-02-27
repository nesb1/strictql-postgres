import pytest

from strictql_postgres.common_types import SupportedQuery


def test_select_query_works() -> None:
    SupportedQuery(query="select * from users")


@pytest.mark.parametrize(
    "query",
    ["update users set name = '123'"],
)
def test_not_suuported_query_raises_error(query: str) -> None:
    with pytest.raises(ValueError):
        SupportedQuery(query=query)
