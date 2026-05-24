"""Mini Git의 저장소 상태와 그래프 연산."""

from __future__ import annotations

from datetime import datetime
import os
import time

from .diff_utils import render_line_diff
from .models import Commit
from .sorting import insertion_sort, merge_sort_custom
from .text_index import normalize_token, split_message_keywords


class MiniGit:
    """브랜치, 커밋, 검색, 순회 로직을 담은 메모리 기반 Mini Git 저장소."""

    def __init__(self) -> None:
        self.initialized = False
        self.author = ""
        self.current_branch = ""
        self.branch_heads_by_name: dict[str, str | None] = {}
        self.commits_by_hash: dict[str, Commit] = {}
        self.commit_order: list[str] = []
        self.children: dict[str, set[str]] = {}
        self.keyword_index: dict[str, list[str]] = {}
        self.author_index: dict[str, list[str]] = {}
        self.next_id = 1

    def init(self, user_name: str) -> list[str]:
        """메모리 기반 저장소를 초기화하거나 재설정한다."""
        self.initialized = True
        self.author = user_name
        self.current_branch = "main"
        self.branch_heads_by_name = {"main": None}
        self.commits_by_hash = {}
        self.commit_order = []
        self.children = {}
        self.keyword_index = {}
        self.author_index = {}
        self.next_id = 1
        return [
            "Initialized repository.",
            "Current branch: main",
            f"Current user: {self.author}",
        ]

    def ensure_initialized(self) -> str | None:
        """명령 실행 전에 저장소가 필요하면 오류 메시지를 반환한다."""
        if not self.initialized:
            return "Repository not initialized"
        return None

    def create_branch(self, name: str) -> list[str]:
        """현재 브랜치 HEAD 위치에 브랜치를 생성한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        if name in self.branch_heads_by_name:
            return [f"Branch already exists: {name}"]
        self.branch_heads_by_name[name] = self.branch_heads_by_name[self.current_branch]
        self.refresh_branch_labels()
        return [f"Created branch: {name}"]

    def switch_branch(self, name: str) -> list[str]:
        """HEAD를 기존 브랜치로 전환한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        if name not in self.branch_heads_by_name:
            return [f"Unknown branch: {name}"]
        self.current_branch = name
        return [f"Switched to branch: {name}"]

    def generate_hash(self) -> str:
        """현재 세션에서 고유한 커밋 해시를 생성한다."""
        while True:
            commit_hash = f"c{self.next_id:06d}"
            self.next_id += 1
            if commit_hash not in self.commits_by_hash:
                return commit_hash

    def commit(
        self,
        message: str,
        parents: list[str] | None = None,
        prefix: str | None = None,
    ) -> list[str]: #parents, prefix는 merge 명령에서 사용하기 위한 선택적 인자입니다.
        """커밋을 생성하고 브랜치 포인터와 역색인을 갱신한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        if parents is None:
            current_head = self.branch_heads_by_name[self.current_branch]
            parents = [] if current_head is None else [current_head]
        commit_hash = self.generate_hash()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit = Commit(
            hash=commit_hash,
            message=message,
            author=self.author,
            timestamp=timestamp,
            parents=list(parents),
            branches=[],
        )
        self.commits_by_hash[commit_hash] = commit
        self.commit_order.append(commit_hash)
        self.children.setdefault(commit_hash, set())
        for parent in parents:
            self.children.setdefault(parent, set()).add(commit_hash)
        self.branch_heads_by_name[self.current_branch] = commit_hash
        self.index_commit(commit)
        self.refresh_branch_labels()
        shown_prefix = prefix if prefix is not None else self.current_branch #prefix는 merge 명령에서 커밋 메시지 앞에 붙는 텍스트입니다. 
        return [f"[{shown_prefix} {commit_hash}] {message}"]

    def index_commit(self, commit: Commit) -> None:
        """새 커밋에 대한 키워드와 작성자 역색인을 갱신한다."""
        author_key = normalize_token(commit.author)
        self.author_index.setdefault(author_key, []).append(commit.hash)
        for keyword in split_message_keywords(commit.message):
            self.keyword_index.setdefault(keyword, []).append(commit.hash)

    def refresh_branch_labels(self) -> None:
        """표시용으로 현재 브랜치 라벨을 커밋에 붙인다."""
        for commit in self.commits_by_hash.values():
            commit.branches = []
        for branch_name in self.branch_heads_by_name:
            head = self.branch_heads_by_name[branch_name]
            if head in self.commits_by_hash:
                self.commits_by_hash[head].branches.append(branch_name)

    def get_ordered_commits(self) -> list[Commit]:
        """부모가 자식보다 먼저 오는 생성 순서로 커밋을 반환한다."""
        ordered = []
        for commit_hash in self.commit_order:
            ordered.append(self.commits_by_hash[commit_hash])
        return ordered

    def log(self, sort_by: str | None = None) -> list[str]:
        """커밋 로그를 부모 우선 순서 또는 요청된 직접 정렬 기준으로 렌더링한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        commits = self.get_ordered_commits()
        if sort_by == "date":
            commits = insertion_sort(commits, lambda commit: (commit.timestamp, commit.hash))
        elif sort_by == "author":
            commits = insertion_sort(commits, lambda commit: (normalize_token(commit.author), commit.hash))
        elif sort_by is not None:
            return ["Invalid args"]
        if not commits:
            return ["No commits"]
        lines = []
        for commit in commits:
            branch_text = f" [{', '.join(commit.branches)}]" if commit.branches else ""
            parent_text = ",".join(commit.parents) if commit.parents else "-"
            lines.append(f"commit {commit.hash} ({commit.author}, {commit.timestamp}){branch_text}")
            lines.append(f"parents: {parent_text}")
            lines.append(commit.message)
        return lines

    def search_keyword(self, keyword: str) -> list[str]:
        """키워드 역색인으로 메시지 키워드를 검색한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        commit_hashes = self.keyword_index.get(normalize_token(keyword), [])
        return self.render_search_results(commit_hashes)

    def search_author(self, author: str) -> list[str]:
        """작성자 역색인으로 커밋 작성자를 검색한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        commit_hashes = self.author_index.get(normalize_token(author), [])
        return self.render_search_results(commit_hashes)

    def render_search_results(self, commit_hashes: list[str]) -> list[str]:
        """색인 검색 결과를 부모 우선 생성 순서로 렌더링한다."""
        if not commit_hashes:
            return ["Found 0 commits."]
        allowed = set(commit_hashes)
        ordered = []
        for commit_hash in self.commit_order:
            if commit_hash in allowed:
                ordered.append(commit_hash)
        lines = [f"Found {len(ordered)} commit{'s' if len(ordered) != 1 else ''}:"]
        for commit_hash in ordered:
            commit = self.commits_by_hash[commit_hash]
            lines.append(f"- {commit.hash}: {commit.message} ({commit.author}, {commit.timestamp})")
        return lines

    def path_between(self, start: str, target: str) -> list[str]:
        """사전식 경로 순서로 동률을 깨며 가장 짧은 무방향 커밋 경로를 찾는다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        if start not in self.commits_by_hash:
            return [f"Unknown commit: {start}"]
        if target not in self.commits_by_hash:
            return [f"Unknown commit: {target}"]
        if start == target:
            return [f"Path: {start}"]
        level = [[start]]
        seen_depth = {start: 0}
        depth = 0
        while level:
            target_paths = []
            next_level = []
            for path in level:
                current = path[-1]
                for neighbor in self.neighbors(current):
                    if neighbor in path:
                        continue
                    candidate = path + [neighbor]
                    if neighbor == target:
                        target_paths.append(candidate)
                    previous_depth = seen_depth.get(neighbor)
                    if previous_depth is None or previous_depth == depth + 1:
                        seen_depth[neighbor] = depth + 1
                        next_level.append(candidate)
            if target_paths:
                target_paths = insertion_sort(target_paths, lambda path: "->".join(path))
                return [f"Path: {' -> '.join(target_paths[0])}"]
            next_level = insertion_sort(next_level, lambda path: "->".join(path))
            level = next_level
            depth += 1
        return ["No path"]

    def neighbors(self, commit_hash: str) -> list[str]:
        """커밋의 무방향 이웃을 사전식 순서로 반환한다."""
        linked = set(self.commits_by_hash[commit_hash].parents)
        linked.update(self.children.get(commit_hash, set()))
        return insertion_sort(list(linked), lambda value: value)

    def ancestors(self, commit_hash: str) -> list[str]:
        """부모 링크를 통해 도달할 수 있는 모든 조상을 반환한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        if commit_hash not in self.commits_by_hash:
            return [f"Unknown commit: {commit_hash}"]
        visited = set()
        output = []
        stack = list(self.commits_by_hash[commit_hash].parents)
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            output.append(current)
            for parent in self.commits_by_hash[current].parents:
                if parent not in visited:
                    stack.append(parent)
        output = insertion_sort(output, lambda value: value)
        if not output:
            return ["No ancestors"]
        lines = [f"Ancestors of {commit_hash}:"]
        for ancestor in output:
            commit = self.commits_by_hash[ancestor]
            lines.append(f"- {commit.hash}: {commit.message}")
        return lines

    def merge(self, branch_name: str) -> list[str]:
        """현재 HEAD와 대상 브랜치 HEAD를 부모로 갖는 병합 커밋을 생성한다."""
        error = self.ensure_initialized()
        if error:
            return [error]
        if branch_name not in self.branch_heads_by_name:
            return [f"Unknown branch: {branch_name}"]
        current_head = self.branch_heads_by_name[self.current_branch]
        target_head = self.branch_heads_by_name[branch_name]
        if current_head is None or target_head is None:
            return ["Invalid args"]
        if current_head == target_head:
            return [f"Already up to date with {branch_name}"]
        parents = [current_head, target_head]
        message = f"Merge branch {branch_name} into {self.current_branch}"
        return self.commit(message, parents=parents, prefix=f"merge {self.current_branch}")

    def diff_files(self, file1: str, file2: str) -> list[str]:
        """두 텍스트 파일을 줄 단위로 비교하고 공통, 삭제, 추가 줄을 표시한다."""
        if not os.path.exists(file1) or not os.path.isfile(file1):
            return [f"Unknown file: {file1}"]
        if not os.path.exists(file2) or not os.path.isfile(file2):
            return [f"Unknown file: {file2}"]
        with open(file1, "r", encoding="utf-8") as handle:
            left = handle.read().splitlines()
        with open(file2, "r", encoding="utf-8") as handle:
            right = handle.read().splitlines()
        return render_line_diff(left, right)

    def benchmark_sorts(self, size: int) -> list[str]:
        """결정적인 역순 입력으로 직접 구현한 두 정렬 알고리즘을 비교한다."""
        if size < 1:
            return ["Invalid args"]
        data = []
        value = size
        while value > 0:
            data.append(value)
            value -= 1
        start = time.perf_counter()
        first = insertion_sort(data, lambda item: item)
        insertion_elapsed = time.perf_counter() - start
        start = time.perf_counter()
        second = merge_sort_custom(data, lambda item: item)
        merge_elapsed = time.perf_counter() - start
        if first != second:
            return ["Sort benchmark failed"]
        return [
            f"Sort benchmark size={size}",
            f"insertion_sort_seconds={insertion_elapsed:.6f}",
            f"merge_sort_seconds={merge_elapsed:.6f}",
        ]
