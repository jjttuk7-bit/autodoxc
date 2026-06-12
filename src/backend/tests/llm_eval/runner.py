"""평가 러너 — pytest fixture 기반.

각 에이전트의 fixture를 순회하며:
1. 에이전트 실행
2. expected.json과 assert_matches (구조 검증)
3. LLM-judge 호출 (rubric 기반 정성 평가; dummy면 baseline)
4. baseline 기록·비교

pytest로 호출:
    cd src/backend
    .venv/Scripts/python.exe -m pytest tests/llm_eval/ -v
"""
from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any

import pytest

from app.config import get_settings
from app.llm import LLMClient, get_llm_client

from .assertions import assert_matches
from .baselines import Baselines, CaseBaseline
from .fixtures_loader import FixtureCase, load_cases
from .judge import judge


def _judge_enabled() -> bool:
    """LLM-judge 호출 기본은 off. LLM_EVAL_USE_JUDGE=1로 명시적 활성화.

    이유: fixture 산출물은 현재 dummy 시드 기반. 실 LLM judge가 시드를
    엄격히 평가해 회귀 거짓 양성이 발생. 본격 LLM 산출물 회귀(B1-6 이후)에서 활성화.
    """
    return os.environ.get("LLM_EVAL_USE_JUDGE", "0") == "1"


# 에이전트별 실행 함수 매핑 — runner가 에이전트 코드에 의존하지 않도록 호출자 측이 등록


AgentRunner = Callable[[dict[str, Any], LLMClient], Awaitable[dict[str, Any]]]


async def run_case(
    case: FixtureCase,
    runner: AgentRunner,
    llm: LLMClient | None = None,
    is_dummy: bool | None = None,
) -> dict[str, Any]:
    """fixture를 실행하고 결과 + 평가 메타 반환."""
    settings = get_settings()
    llm = llm or get_llm_client(settings)
    is_dummy = (
        is_dummy if is_dummy is not None else settings.llm_mode == "dummy"
    )

    actual = await runner(case.input, llm)

    a_result = (
        assert_matches(case.expected, actual)
        if case.expected is not None
        else None
    )
    # judge는 기본 비활성 (baseline 0.85 반환). LLM_EVAL_USE_JUDGE=1로 활성화.
    j_result = await judge(
        llm=llm,
        agent=case.agent,
        output=actual,
        is_dummy=is_dummy or not _judge_enabled(),
    )

    pass_count = len(a_result.passed) if a_result else 0
    fail_count = len(a_result.failed) if a_result else 0
    baselines = Baselines.load()
    key = f"{case.agent}/{case.case_id}"
    baselines.upsert(
        key,
        CaseBaseline(
            case_id=key,
            assertion_pass=pass_count,
            assertion_fail=fail_count,
            judge_score=j_result.score,
        ),
    )
    baselines.save()

    return {
        "actual": actual,
        "assertion": a_result.report() if a_result else "no expected.json",
        "assertion_ok": a_result.ok if a_result else True,
        "judge_score": j_result.score,
        "judge_comment": j_result.comment,
    }


# --- pytest 통합 -----------------------------------------------------------


def parametrize_fixtures(agent: str):
    cases = load_cases(agent)
    return pytest.mark.parametrize(
        "case", cases, ids=[c.case_id for c in cases]
    )
