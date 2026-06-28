"""pytest 진입점 — 에이전트별 fixture 평가."""
from __future__ import annotations

from typing import Any

import pytest

from app.agents import DocTypeIdentifier, FactsExtractor, SkeletonComposer
from app.llm import LLMClient
from app.llm.adapter import DummyLLMClient
from app.llm.factory import _dummy_responder
from app.shared.types.agents.doc_type_identifier import DocTypeIdentifierInput
from app.shared.types.agents.facts_extractor import FactsExtractorInput
from app.shared.types.agents.skeleton_composer import SkeletonComposerInput

from .fixtures_loader import FixtureCase, load_cases
from .runner import run_case


# --- runner adapters ------------------------------------------------------


async def _run_doc_type_identifier(
    payload: dict[str, Any], llm: LLMClient
) -> dict[str, Any]:
    agent = DocTypeIdentifier(llm)
    out = await agent.run(DocTypeIdentifierInput.model_validate(payload))
    return out.model_dump()


async def _run_skeleton_composer(
    payload: dict[str, Any], llm: LLMClient
) -> dict[str, Any]:
    agent = SkeletonComposer(llm)
    out = await agent.run(SkeletonComposerInput.model_validate(payload))
    return out.model_dump()


async def _run_facts_extractor(
    payload: dict[str, Any], llm: LLMClient
) -> dict[str, Any]:
    agent = FactsExtractor(llm)
    out = await agent.run(FactsExtractorInput.model_validate(payload))
    return out.model_dump()


_RUNNERS = {
    "doc_type_identifier": _run_doc_type_identifier,
    "skeleton_composer": _run_skeleton_composer,
    "facts_extractor": _run_facts_extractor,
}


# --- parametrize ----------------------------------------------------------


def _collect_all_cases() -> list[FixtureCase]:
    all_cases: list[FixtureCase] = []
    for agent in _RUNNERS:
        all_cases.extend(load_cases(agent))
    return all_cases


CASES = _collect_all_cases()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[f"{c.agent}/{c.case_id}" for c in CASES],
)
async def test_agent_fixture(case: FixtureCase) -> None:
    runner = _RUNNERS[case.agent]
    # fixture 산출물은 dummy 시드 기반 → 로컬에 실제 키가 있어도 dummy로 고정해
    # 결정적으로 평가 (실 LLM 분류 회귀는 별도 prod 검증으로 확인).
    result = await run_case(
        case, runner, llm=DummyLLMClient(_dummy_responder), is_dummy=True
    )

    # assertion 결과 출력 (pytest -v로 보기)
    print(f"\n=== {case.agent}/{case.case_id} ===")
    print(f"assertion: {result['assertion']}")
    print(f"judge: {result['judge_score']:.2f} — {result['judge_comment']}")

    assert result["assertion_ok"], result["assertion"]
    assert result["judge_score"] >= 0.7, (
        f"judge score {result['judge_score']:.2f} below threshold"
    )
