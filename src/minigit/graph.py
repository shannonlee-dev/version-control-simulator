"""커밋 그래프의 이웃·최단 경로·조상 탐색."""

from .models import Commit
from .sorting import insertion_sort


def neighbors(
    commits: dict[str, Commit], children: dict[str, set[str]], commit_hash: str
) -> list[str]:
    """커밋의 무방향 이웃을 사전식 순서로 반환한다."""
    linked = set(commits[commit_hash].parents)
    linked.update(children.get(commit_hash, set()))
    return insertion_sort(list(linked), lambda value: value)


def path_between(
    commits: dict[str, Commit], children: dict[str, set[str]], start: str, target: str
) -> list[str]:
    """사전식 경로 순서로 동률을 깨며 가장 짧은 무방향 커밋 경로를 찾는다."""
    if start not in commits:
        return [f"Unknown commit: {start}"]
    if target not in commits:
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
            for neighbor in neighbors(commits, children, current):
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


def ancestors(commits: dict[str, Commit], commit_hash: str) -> list[str]:
    """부모 링크를 통해 도달할 수 있는 모든 조상을 반환한다."""
    if commit_hash not in commits:
        return [f"Unknown commit: {commit_hash}"]
    visited = set()
    output = []
    stack = list(commits[commit_hash].parents)
    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        output.append(current)
        for parent in commits[current].parents:
            if parent not in visited:
                stack.append(parent)
    output = insertion_sort(output, lambda value: value)
    if not output:
        return ["No ancestors"]
    lines = [f"Ancestors of {commit_hash}:"]
    for ancestor in output:
        commit = commits[ancestor]
        lines.append(f"- {commit.hash}: {commit.message}")
    return lines
