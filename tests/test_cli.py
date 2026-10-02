"""별도 REPL에서 초기화·브랜치·검색·그래프·병합과 이동한 diff 샘플을 확인한다."""

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
    assert "Invalid args" not in result.stdout and "File not found" not in result.stdout
