import pathlib

from strictql_postgres.dir_diff import get_diff_for_changed_files, get_missed_files


def test_files_diff_works() -> None:
    diff_for_changed_files = get_diff_for_changed_files(
        {
            pathlib.Path("a"): "content1\nkek\n",
            pathlib.Path("c"): "c content",
            pathlib.Path("d"): "same content",
        },
        expected={
            pathlib.Path("a"): "content\nkek123\n",
            pathlib.Path("b"): "b content",
            pathlib.Path("d"): "same content",
        },
    )

    assert diff_for_changed_files == {
        pathlib.Path("a"): """--- 

+++ 

@@ -1,2 +1,2 @@

-content
-kek123
+content1
+kek""",
    }


def test_get_missed_files() -> None:
    missed_files = get_missed_files(
        {
            pathlib.Path("a"): "content",
            pathlib.Path("c"): "content",
        },
        expected={
            pathlib.Path("a"): "content",
            pathlib.Path("b"): "content",
            pathlib.Path("d"): "content",
        },
    )

    assert missed_files == {
        pathlib.Path("b"),
        pathlib.Path("d"),
    }
