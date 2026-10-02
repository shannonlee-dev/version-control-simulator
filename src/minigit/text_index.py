"""Mini Git 검색 인덱스를 위한 텍스트 정규화 도우미."""

from __future__ import annotations


def normalize_token(token: str) -> str:
    """대소문자를 구분하지 않는 조회를 위해 사용자 텍스트와 메시지 키워드를 정규화한다."""
    return token.strip().lower()


def split_message_keywords(message: str) -> list[str]:
    """커밋 메시지를 정규화된 키워드 토큰으로 나눈다."""
    tokens = []
    seen = set()
    for raw in message.split():
        token = normalize_token(raw)
        if token and token not in seen:
            seen.add(token)
            tokens.append(token)
    return tokens
