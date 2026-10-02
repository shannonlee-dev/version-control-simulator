"""별도 REPL에서 초기화·브랜치·검색·그래프·병합과 이동한 diff 샘플을 확인한다."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.smoke


def test_version_control_repl_commands():
    commands = "\n".join(
        [
            'init "검증 사용자"',
            'commit "첫 기록"',
            "branch feature",
            "switch feature",
            'commit "검색 기능"',
            "switch main",
            'commit "기본 변경"',
            "path c000002 c000003",
            "search 검색",
            "merge feature",
            "log",
            "diff examples/diff/a.txt examples/diff/b.txt",
            "quit",
            "",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-m", "minigit"],
        input=commands,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert "c000002 -> c000001 -> c000003" in result.stdout
    assert "검색 기능" in result.stdout and "c000004" in result.stdout
    assert "Invalid args" not in result.stdout and "Unknown file" not in result.stdout
    diff = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout).split("Diff:\n", 1)[1]
    assert diff.split("mini-git>", 1)[0].splitlines() == [
        "  ha",
        "- ho",
        "  hi",
        "- eof",
        "+ hi",
        "+ of",
    ]


def test_missing_diff_file_reports_error_and_repl_continues(tmp_path):
    missing = tmp_path / "missing.txt"
    result = subprocess.run(
        [sys.executable, "-m", "minigit"],
        input=f'diff "{missing}" examples/diff/b.txt\ninit User\ncommit "After error"\nquit\n',
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert f"Unknown file: {missing}" in result.stdout
    assert "c000001] After error" in result.stdout and "Bye." in result.stdout
