"""Assertion 헬퍼 — fixture의 expected와 결과 모델을 비교.

비교 정책:
- expected의 모든 키가 actual에 존재해야 함 (subset 매칭)
- 값은 deep-equal (리스트는 순서 있음)
- None / 누락 키는 "관심 없음" — actual의 추가 키는 허용
- `__contains__` 슈가: expected에 "field": {"__contains": "X"}면 부분 문자열 매칭
"""
from __future__ import annotations

from typing import Any


class AssertionResult:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []

    def add_pass(self, path: str) -> None:
        self.passed.append(path)

    def add_fail(self, path: str, msg: str) -> None:
        self.failed.append(f"{path}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.failed

    def report(self) -> str:
        ok = len(self.passed)
        bad = len(self.failed)
        head = f"{ok} passed, {bad} failed"
        if not self.failed:
            return head
        return head + "\n  - " + "\n  - ".join(self.failed)


def _matches(expected: Any, actual: Any, path: str, result: AssertionResult) -> None:
    if isinstance(expected, dict):
        if "__contains" in expected:
            target = expected["__contains"]
            if isinstance(actual, str) and target in actual:
                result.add_pass(path)
            else:
                result.add_fail(path, f"expected substring {target!r}, got {actual!r}")
            return
        if not isinstance(actual, dict):
            result.add_fail(path, f"expected dict, got {type(actual).__name__}")
            return
        for key, sub_expected in expected.items():
            if key not in actual:
                result.add_fail(f"{path}.{key}", "missing")
                continue
            _matches(sub_expected, actual[key], f"{path}.{key}", result)
        return

    if isinstance(expected, list):
        if not isinstance(actual, list):
            result.add_fail(path, f"expected list, got {type(actual).__name__}")
            return
        if len(expected) > len(actual):
            result.add_fail(
                path, f"expected at least {len(expected)} items, got {len(actual)}"
            )
            return
        for i, exp_item in enumerate(expected):
            _matches(exp_item, actual[i], f"{path}[{i}]", result)
        return

    if expected == actual:
        result.add_pass(path)
    else:
        result.add_fail(path, f"expected {expected!r}, got {actual!r}")


def assert_matches(expected: dict[str, Any], actual: dict[str, Any]) -> AssertionResult:
    result = AssertionResult()
    _matches(expected, actual, "$", result)
    return result
