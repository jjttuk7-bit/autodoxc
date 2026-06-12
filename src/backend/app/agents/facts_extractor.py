"""#2 FactsExtractor — 사용자 자유 입력에서 사실 추출.

데모: 단순 정규식 + 키워드로 핵심 사실만 추출.
B1에서 LLM 기반 풀 구현으로 교체.
"""
from __future__ import annotations

import re

from app.llm import LLMClient
from app.shared.types import Fact
from app.shared.types.agents.facts_extractor import (
    FactsExtractorInput,
    FactsExtractorOutput,
)


_NUMBER_PATTERN = re.compile(r"(\d+)\s*(명|회|개|건|년|개월|%)")


class FactsExtractor:
    name = "facts_extractor"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(self, input: FactsExtractorInput) -> FactsExtractorOutput:
        facts: list[Fact] = []

        # 모든 사용자 발화를 합쳐서 검색
        text = "\n".join(m.text for m in input.user_input_history if m.role == "user")

        # 단순 패턴 추출: 수치
        for match in _NUMBER_PATTERN.finditer(text):
            num, unit = match.group(1), match.group(2)
            facts.append(
                Fact(
                    field_id=f"quant:{unit}",
                    value=int(num),
                    source="explicit",
                    confidence=0.85,
                    rationale=f"입력 텍스트에서 '{match.group(0)}' 패턴 추출",
                )
            )

        # 키워드 기반 추출 (도메인별 — 콜드스타트용 최소)
        if "항공우주" in text or "5축" in text:
            facts.append(
                Fact(
                    field_id="industry",
                    value="항공우주 부품 제조 / 5축 가공",
                    source="explicit",
                    confidence=0.9,
                )
            )
        if "특수 합금" in text or "특수합금" in text:
            facts.append(
                Fact(
                    field_id="core_skill",
                    value="특수 합금 가공 노하우",
                    source="explicit",
                    confidence=0.9,
                )
            )

        return FactsExtractorOutput(facts=facts)
