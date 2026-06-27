"""#1b SkeletonComposer — 문서 종류에서 골격 구성.

콜드스타트(DA1·DA2·DA3 비어있음): 시드 우선 → 없으면 LLM 호출.
01-agents.md의 4개 소스 우선순위는 자산 구축 후 활성화.
"""
from __future__ import annotations

import json
import logging
import re

from app.llm import LLMClient
from app.llm.prompts import SKELETON_SYSTEM
from app.shared.errors import format_exception_chain as _format_error
from app.shared.types import DocType, SkeletonNode, SourceLlmInference
from app.shared.types.agents.skeleton_composer import (
    CompositionContribution,
    CompositionMeta,
    SkeletonComposerInput,
    SkeletonComposerOutput,
)


# 콜드스타트 시드 — 외국인 고용 계획서 1종만 하드코딩 (M5의 시드 큐레이션 전)
_SEED_SKELETONS: dict[str, list[tuple[str, str, str, str]]] = {
    "foreign-worker-employment-plan": [
        (
            "sec_1",
            "1. 고용 대상 업종",
            "업종 정의 및 산업 기술 발전 현시점 상징성",
            "어떤 업종이고 왜 이 인력이 산업적으로 의미 있는가?",
        ),
        (
            "sec_2",
            "2. 고용 사유",
            "국내 채용 노력 + 기술 부채 및 시장 구조적 문제",
            "왜 국내에서 못 찾았고, 그것이 시스템적 문제인가?",
        ),
        (
            "sec_3",
            "3. 기술도입 및 고용 효과",
            "생산 효율·품질·시장 경쟁 우위 정량 효과",
            "고용 시 어떤 정량적 효과가 기대되는가?",
        ),
        (
            "sec_4",
            "4. 활용 계획",
            "단기/장기 로드맵 + 기술 이전 방법론",
            "이 인력을 어떻게 활용해 회사·국내 산업에 기여할 것인가?",
        ),
        (
            "sec_5",
            "5. 기타사항",
            "기술 주권 확보 및 일자리 질적 향상 등 거시 파급",
            "거시적 관점에서 어떤 파급 효과가 있는가?",
        ),
    ],
    "content-certified-mail": [
        ("sec_1", "1. 수신·발신인 표시", "수신인·발신인 식별", "당사자가 누구인가?"),
        ("sec_2", "2. 사실관계", "분쟁 사실 시간순 정리", "무슨 일이 있었는가?"),
        ("sec_3", "3. 법적 근거", "관련 법령·계약 조항 인용", "법적 근거는 무엇인가?"),
        ("sec_4", "4. 요구 사항", "이행 또는 시정 요구", "상대방에게 무엇을 요구하는가?"),
        ("sec_5", "5. 기한 및 효과", "이행 기한 + 미이행 시 조치", "기한·효과는?"),
    ],
    "administrative-appeal": [
        ("sec_1", "1. 당사자", "청구인 / 피청구인 표시", "누가 누구를 상대로 청구하는가?"),
        ("sec_2", "2. 처분의 내용", "어떤 처분에 대한 이의인가", "처분 일자·내용·근거 법령"),
        ("sec_3", "3. 청구 취지", "무엇을 취소·변경·확인하길 요구하는가", "구체적 청구 사항"),
        ("sec_4", "4. 청구 이유", "IRAC — 쟁점·근거조항·적용·결론", "왜 처분이 위법·부당한가?"),
        ("sec_5", "5. 증거방법", "첨부 증거 목록", "무엇으로 입증하는가?"),
    ],
}


logger = logging.getLogger(__name__)


def _llm_inferred_source(confidence: float = 0.6) -> SourceLlmInference:
    return SourceLlmInference(confidence=confidence)


class SkeletonComposer:
    name = "skeleton_composer"

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.last_error: str | None = None  # LLM 폴백 사유 (진단·UX 노출용)

    async def run(
        self, input: SkeletonComposerInput
    ) -> SkeletonComposerOutput:
        doc_type = input.doc_type
        seed = _SEED_SKELETONS.get(doc_type.id)

        if seed:
            source = _llm_inferred_source(confidence=0.85)
            nodes = [
                SkeletonNode(
                    id=sid,
                    title=title,
                    role=role,
                    logic_anchor=anchor,
                    source=source,
                )
                for sid, title, role, anchor in seed
            ]
            return SkeletonComposerOutput(
                skeleton=nodes,
                composition_meta=CompositionMeta(
                    primary_source=source,
                    contributions=[
                        CompositionContribution(
                            source=source,
                            sections=[n.id for n in nodes],
                        )
                    ],
                ),
            )

        # 시드 없음 → LLM 호출
        return await self._compose_via_llm(doc_type)

    async def _compose_via_llm(self, doc_type: DocType) -> SkeletonComposerOutput:
        user_msg = (
            f"문서 종류: {doc_type.ko_name}\n"
            f"canonical id: {doc_type.id}\n"
            f"도메인: {doc_type.domain}\n"
            f"분류: {' > '.join(doc_type.taxonomy_path) if doc_type.taxonomy_path else '미분류'}\n\n"
            f"위 문서의 5개 섹션 골격을 JSON으로 설계하라."
        )
        try:
            result = await self.llm.run_json(
                tier="sonnet", system=SKELETON_SYSTEM, user=user_msg, max_tokens=1024
            )
            data = _parse_json(result.text)
            sections = data.get("sections", []) if isinstance(data, dict) else []
            nodes = _to_skeleton_nodes(sections)
            if nodes:
                source = _llm_inferred_source(confidence=0.7)
                return SkeletonComposerOutput(
                    skeleton=nodes,
                    composition_meta=CompositionMeta(
                        primary_source=source,
                        contributions=[
                            CompositionContribution(
                                source=source, sections=[n.id for n in nodes]
                            )
                        ],
                    ),
                )
            self.last_error = "LLM 응답에서 섹션을 추출하지 못함"
            logger.warning(
                "SkeletonComposer 폴백: %s — model=%s raw=%.200s",
                self.last_error, result.model, result.text,
            )
        except Exception as e:
            self.last_error = _format_error(e)
            logger.exception("SkeletonComposer LLM 호출 실패 → stub 폴백")

        # 최종 폴백 — 5섹션 stub
        source = _llm_inferred_source(confidence=0.3)
        nodes = [
            SkeletonNode(
                id=f"sec_{i + 1}",
                title=f"{i + 1}. (섹션 {i + 1})",
                role="(추론)",
                logic_anchor=f"섹션 {i + 1}의 논점은?",
                source=source,
            )
            for i in range(5)
        ]
        return SkeletonComposerOutput(
            skeleton=nodes,
            composition_meta=CompositionMeta(
                primary_source=source,
                contributions=[
                    CompositionContribution(
                        source=source, sections=[n.id for n in nodes]
                    )
                ],
            ),
        )


# --- 파싱 헬퍼 -----------------------------------------------------------


def _parse_json(text: str) -> dict | list | None:
    """LLM 응답에서 JSON 추출. 코드 블록 감싸진 경우도 처리."""
    text = text.strip()
    # ```json ... ``` 또는 ``` ... ``` 제거
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 시작이 { 또는 [ 인 부분만 추출 시도
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None


def _to_skeleton_nodes(sections: list) -> list[SkeletonNode]:
    nodes: list[SkeletonNode] = []
    source = _llm_inferred_source(confidence=0.7)
    for i, sec in enumerate(sections[:5]):
        if not isinstance(sec, dict):
            continue
        sid = str(sec.get("id") or f"sec_{i + 1}")
        title = str(sec.get("title") or f"{i + 1}. (섹션 {i + 1})")
        role = str(sec.get("role") or "")
        anchor = str(sec.get("logic_anchor") or "")
        nodes.append(
            SkeletonNode(
                id=sid, title=title, role=role, logic_anchor=anchor, source=source
            )
        )
    return nodes
