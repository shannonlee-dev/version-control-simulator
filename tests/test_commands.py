"""문서에서 안내하는 정렬·검색·벤치마크와 오류 처리의 공개 동작."""

import pytest

from minigit.cli import execute
from minigit.repository import MiniGit
from minigit.sorting import insertion_sort, merge_sort_custom


@pytest.mark.parametrize(
    "command",
    [
        "",
        'commit "unterminated',
        "commit",
        "log --sort-by=unknown",
        "search one two",
        "branch",
        "switch",
        "merge",
        "diff one",
        "bench-sort bad",
        "bench-sort 0",
    ],
)
def test_invalid_command_keeps_existing_history(command):
    repository = MiniGit()
    execute(repository, "INIT User")
    execute(repository, 'COMMIT "Original"')
    assert execute(repository, command) == (True, ["Invalid args"])
    assert repository.commit_order == ["c000001"]
    assert repository.branch_heads_by_name == {"main": "c000001"}


def test_log_sort_options_and_case_insensitive_author_search():
    repository = MiniGit()
    repository.init("Zoe")
    repository.commit("First")
    repository.author = "Alice"
    repository.commit("Second")
    repository.commits_by_hash["c000001"].timestamp = "2024-02-01 00:00:00"
    repository.commits_by_hash["c000002"].timestamp = "2024-01-01 00:00:00"
    assert execute(repository, "log")[1][0].startswith("commit c000001")
    for command in ["log --sort-by=date", "log --sort-by=author"]:
        rows = execute(repository, command)[1]
        assert rows[0].startswith("commit c000002")
        assert rows[3].startswith("commit c000001")
    rows = execute(repository, "SEARCH --author=ALICE")[1]
    assert rows[0] == "Found 1 commit:" and "c000002: Second" in rows[1]
    assert execute(repository, "search first")[1][0] == "Found 1 commit:"


def test_empty_branch_and_unknown_merge_keep_heads_unchanged():
    repository = MiniGit()
    repository.init("User")
    repository.create_branch("empty")
    repository.commit("First")
    assert execute(repository, "merge empty") == (True, ["Invalid args"])
    assert execute(repository, "merge missing") == (True, ["Unknown branch: missing"])
    assert execute(repository, "merge main") == (True, ["Already up to date with main"])
    assert repository.commit_order == ["c000001"]
    assert repository.branch_heads_by_name == {"main": "c000001", "empty": None}


@pytest.mark.parametrize("command,size", [("bench-sort", 100), ("bench-sort 20", 20)])
def test_sort_benchmark_reports_both_algorithms(command, size):
    rows = execute(MiniGit(), command)[1]
    assert rows[0] == f"Sort benchmark size={size}"
    assert rows[1].startswith("insertion_sort_seconds=")
    assert rows[2].startswith("merge_sort_seconds=")
    assert all(float(row.split("=", 1)[1]) >= 0 for row in rows[1:])


@pytest.mark.parametrize("sorter", [insertion_sort, merge_sort_custom])
def test_sorting_preserves_equal_key_order_without_changing_input(sorter):
    items = [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
    assert sorter(items, lambda item: item[0]) == [
        (1, "b"),
        (1, "d"),
        (2, "a"),
        (2, "c"),
    ]
    assert items == [(2, "a"), (1, "b"), (2, "c"), (1, "d")]
