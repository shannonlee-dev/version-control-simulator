"""Mini Git의 명령 파싱, 실행 분기, REPL."""

from __future__ import annotations

import shlex

from .repository import MiniGit


def parse_command(line: str) -> list[str] | None:
    """셸과 비슷한 따옴표 규칙으로 REPL 한 줄을 파싱한다."""
    try:
        return shlex.split(line)
    except ValueError:
        return None


def execute(repository: MiniGit, line: str) -> tuple[bool, list[str]]:
    """Mini Git 명령 하나를 실행하고 REPL을 계속할지 여부를 반환한다."""
    parts = parse_command(line)
    if parts is None or not parts:
        return True, ["Invalid args"]
    command = parts[0].lower()
    args = parts[1:]

    if command in {"exit", "quit"}:
        return False, ["Bye."]
    if command == "init":
        if len(args) != 1:
            return True, ["Invalid args"]
        return True, repository.init(args[0])
    if command == "branch":
        if len(args) != 1:
            return True, ["Invalid args"]
        return True, repository.create_branch(args[0])
    if command == "switch":
        if len(args) != 1:
            return True, ["Invalid args"]
        return True, repository.switch_branch(args[0])
    if command == "commit":
        if len(args) != 1:
            return True, ["Invalid args"]
        return True, repository.commit(args[0])
    if command == "log":
        if len(args) == 0:
            return True, repository.log()
        if len(args) == 1 and args[0].startswith("--sort-by="):
            return True, repository.log(args[0].split("=", 1)[1].lower())
        return True, ["Invalid args"]
    if command == "path":
        if len(args) != 2:
            return True, ["Invalid args"]
        return True, repository.path_between(args[0], args[1])
    if command == "ancestors":
        if len(args) != 1:
            return True, ["Invalid args"]
        return True, repository.ancestors(args[0])
    if command == "search":
        # search 명령은 --author=이름 또는 키워드 중 하나만 받는다.
        if len(args) != 1:
            return True, ["Invalid args"]
        # --author= 옵션이면 작성자 인덱스로 검색한다.
        if args[0].startswith("--author="):
            return True, repository.search_author(args[0].split("=", 1)[1])
        # 그 외에는 커밋 메시지 키워드로 검색한다.
        return True, repository.search_keyword(args[0])
    if command == "diff":
        if len(args) != 2:
            return True, ["Invalid args"]
        return True, repository.diff_files(args[0], args[1])
    if command == "merge":
        if len(args) != 1:
            return True, ["Invalid args"]
        return True, repository.merge(args[0])
    if command == "bench-sort":
        if len(args) > 1:
            return True, ["Invalid args"]
        try:
            size = int(args[0]) if args else 100
        except ValueError:
            return True, ["Invalid args"]
        return True, repository.benchmark_sorts(size)
    return True, ["Invalid args"]


def repl() -> None:
    """Mini Git REPL을 실행한다."""
    repository = MiniGit()
    while True:
        try:
            line = input("mini-git> ")
        except EOFError:
            print()
            break
        keep_running, output = execute(repository, line)
        for item in output:
            print(item)
        if not keep_running:
            break
