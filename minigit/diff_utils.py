"""Mini Git의 선택 diff 명령을 위한 줄 단위 차이 렌더링."""

from __future__ import annotations


GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"


def _green(text: str) -> str:
    return f"{GREEN}{text}{RESET}"


def _red(text: str) -> str:
    return f"{RED}{text}{RESET}"


def render_line_diff(left: list[str], right: list[str]) -> list[str]:
    """LCS 기반의 간단한 줄 단위 차이를 렌더링한다."""
    rows = len(left) + 1
    cols = len(right) + 1
    table = []
    row = 0
    while row < rows:
        table.append([0] * cols)
        row += 1
    i = len(left) - 1
    while i >= 0:
        j = len(right) - 1
        while j >= 0:
            if left[i] == right[j]:
                table[i][j] = 1 + table[i + 1][j + 1]
            elif table[i + 1][j] >= table[i][j + 1]:
                table[i][j] = table[i + 1][j]
            else:
                table[i][j] = table[i][j + 1]
            j -= 1
        i -= 1
    lines = ["Diff:"]
    i = 0
    j = 0
    while i < len(left) and j < len(right):
        if left[i] == right[j]:
            lines.append(f"  {left[i]}")
            i += 1
            j += 1
        elif table[i + 1][j] >= table[i][j + 1]:
            lines.append(_red(f"- {left[i]}"))
            i += 1
        else:
            lines.append(_green(f"+ {right[j]}"))
            j += 1
    while i < len(left):
        lines.append(_red(f"- {left[i]}"))
        i += 1
    while j < len(right):
        lines.append(_green(f"+ {right[j]}"))
        j += 1
    return lines
