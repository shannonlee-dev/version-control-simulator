"""Mini Git에서 사용하는 직접 구현 정렬 도우미."""

from __future__ import annotations

from typing import Callable, TypeVar


T = TypeVar("T")


def compare_values(left, right) -> int:
    """표준 정렬 도우미 없이 파이썬 비교로 -1, 0, 1을 반환한다."""
    if left < right:
        return -1
    if left > right:
        return 1
    return 0


def insertion_sort(items: list[T], key_func: Callable[[T], object]) -> list[T]:
    """로그, 해시, 경로, 벤치마크 비교에 사용하는 안정 삽입 정렬."""
    result = list(items)
    index = 1
    while index < len(result):
        current = result[index]
        current_key = key_func(current)
        scan = index - 1
        while scan >= 0 and compare_values(key_func(result[scan]), current_key) > 0:
            result[scan + 1] = result[scan]
            scan -= 1
        result[scan + 1] = current
        index += 1
    return result


def merge_sort_custom(items: list[T], key_func: Callable[[T], object]) -> list[T]:
    """보너스 시간 비교를 위해 직접 구현한 안정 병합 정렬."""
    if len(items) <= 1:
        return list(items)
    midpoint = len(items) // 2
    left = merge_sort_custom(items[:midpoint], key_func)
    right = merge_sort_custom(items[midpoint:], key_func)
    merged = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        if compare_values(key_func(left[left_index]), key_func(right[right_index])) <= 0:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1
    while left_index < len(left):
        merged.append(left[left_index])
        left_index += 1
    while right_index < len(right):
        merged.append(right[right_index])
        right_index += 1
    return merged
