"""#1a DocTypeIdentifier — 사용자 입력에서 문서 종류 식별.

콜드스타트(DA1·DA2 비어있음)에서는 LLM 일반 지식에만 의존.
Dummy 모드는 키워드 매칭으로 결정.
"""
from __future__ import annotations

from app.llm import LLMClient, tier_for_agent
from app.shared.types import DocType
from app.shared.types.agents.doc_type_identifier import (
    DocTypeIdentifierInput,
    DocTypeIdentifierOutput,
)


_KEYWORD_MAP: dict[str, DocType] = {
    "외국인": DocType(
        id="foreign-worker-employment-plan",
        ko_name="전문 외국 인력 고용 계획서",
        domain="permit",
        taxonomy_path=["고용", "외국인", "전문인력"],
    ),
    "내용증명": DocType(
        id="content-certified-mail",
        ko_name="내용증명",
        domain="dispute",
        taxonomy_path=["분쟁", "통지"],
    ),
    "행정심판": DocType(
        id="administrative-appeal",
        ko_name="행정심판 청구서",
        domain="dispute",
        taxonomy_path=["분쟁", "구제"],
    ),
}


_DEFAULT = DocType(
    id="generic-administrative-doc",
    ko_name="행정문서 일반",
    domain="other",
    taxonomy_path=["일반"],
)


class DocTypeIdentifier:
    name = "doc_type_identifier"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(
        self, input: DocTypeIdentifierInput
    ) -> DocTypeIdentifierOutput:
        text = input.user_input

        # 1차: 키워드 매칭 (모드 무관)
        for kw, dt in _KEYWORD_MAP.items():
            if kw in text:
                return DocTypeIdentifierOutput(
                    doc_type=dt,
                    confidence=0.92,
                    signals=[f"키워드:{kw}"],
                )

        # 2차: LLM 호출 — 구조화 응답 파싱 부담 줄이려 dummy 흐름에서는 default
        # 실제 LLM 모드에서도 응답 파싱 실패 시 default로 폴백
        try:
            result = await self.llm.run_text(
                tier=tier_for_agent("doc_type_identifier"),
                system=(
                    "당신은 한국 행정문서 분류 전문가다. "
                    "사용자 입력에서 작성하려는 문서 종류를 한 단어 또는 짧은 명칭으로 답하라."
                ),
                user=f"입력: {text}\n\n문서 종류 명칭 1개만:",
                max_tokens=64,
            )
            # 단순 fallback: 응답 텍스트에 키워드가 있으면 매칭, 아니면 default
            for kw, dt in _KEYWORD_MAP.items():
                if kw in result.text:
                    return DocTypeIdentifierOutput(
                        doc_type=dt,
                        confidence=0.7,
                        signals=[f"LLM:{result.model}", f"키워드:{kw}"],
                    )
        except Exception as e:
            return DocTypeIdentifierOutput(
                doc_type=_DEFAULT,
                confidence=0.3,
                signals=[f"LLM 실패: {type(e).__name__}"],
            )

        return DocTypeIdentifierOutput(
            doc_type=_DEFAULT,
            confidence=0.3,
            signals=["키워드 없음, default 강등"],
        )
