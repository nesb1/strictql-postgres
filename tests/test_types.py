import pytest

from strictql_postgres.common_types import SelectQuery


def test_select_query_works() -> None:
    SelectQuery(query="select * from users")


@pytest.mark.parametrize(
    "query", ["delete from users", "update users set name = '123'"]
)
def test_select_query_raises_error(query: str) -> None:
    with pytest.raises(ValueError):
        SelectQuery(query=query)
