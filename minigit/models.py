"""Mini Git의 데이터 모델."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Commit:
    """Mini Git DAG의 커밋 노드."""

    hash: str
    message: str
    author: str
    timestamp: str
    parents: list[str]
    branches: list[str]
