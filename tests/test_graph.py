"""그래프 모듈과 저장소의 경로·부모·색인 계약을 검증한다."""

from minigit.repository import MiniGit


def test_diamond_path_is_shortest_and_lexicographic():
    repository = MiniGit()
    repository.init("사용자")
    repository.commit("공통")
    repository.create_branch("feature")
    repository.commit("기본")
    repository.switch_branch("feature")
    repository.commit("기능")
    repository.switch_branch("main")
    repository.merge("feature")
    assert repository.path_between("c000002", "c000003") == [
        "Path: c000002 -> c000001 -> c000003"
    ]
    assert repository.commits_by_hash["c000004"].parents == ["c000002", "c000003"]
    assert repository.ancestors("c000004")[1:] == [
        "- c000001: 공통",
        "- c000002: 기본",
        "- c000003: 기능",
    ]


def test_unknown_commits_and_reset_clear_indexes():
    repository = MiniGit()
    assert repository.path_between("a", "b") == ["Repository not initialized"]
    repository.init("작성자")
    repository.commit("검색 키워드")
    assert repository.search_keyword("검색")[0] == "Found 1 commit:"
    assert repository.path_between("missing", "c000001") == ["Unknown commit: missing"]
    repository.init("새 작성자")
    assert repository.search_keyword("검색") == ["Found 0 commits."]
    assert repository.commits_by_hash == {} and repository.next_id == 1
