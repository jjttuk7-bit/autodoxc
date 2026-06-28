"""#1a DocTypeIdentifier — 사용자 입력에서 문서 종류 식별.

1) 시드 키워드 빠른 경로 (외국인·내용증명·행정심판) — LLM 없이 즉시.
2) 그 외에는 LLM 구조화 분류(run_json)로 ko_name·domain·id를 직접 도출.
   → SkeletonComposer가 generic "행정문서 일반"이 아니라 실제 문서 종류 기반으로
     골격을 구성하게 한다.
"""
from __future__ import annotations

import json
import re

from app.llm import LLMClient, tier_for_agent
from app.llm.prompts import DOC_TYPE_SYSTEM
from app.shared.types import DocType
from app.shared.types.agents.doc_type_identifier import (
    DocTypeIdentifierInput,
    DocTypeIdentifierOutput,
)
from app.shared.types.primitives import Domain


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

_VALID_DOMAINS: set[str] = {"dispute", "permit", "internal", "other"}


class DocTypeIdentifier:
    name = "doc_type_identifier"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def run(
        self, input: DocTypeIdentifierInput
    ) -> DocTypeIdentifierOutput:
        text = input.user_input

        # 1차: 키워드 매칭 (시드 빠른 경로, 모드 무관)
        for kw, dt in _KEYWORD_MAP.items():
            if kw in text:
                return DocTypeIdentifierOutput(
                    doc_type=dt,
                    confidence=0.92,
                    signals=[f"키워드:{kw}"],
                )

        # 2차: LLM 구조화 분류
        try:
            result = await self.llm.run_json(
                tier=tier_for_agent("doc_type_identifier"),
                system=DOC_TYPE_SYSTEM,
                user=f"입력: {text}\n\n위 문서의 종류를 JSON으로 분류하라.",
                max_tokens=256,
            )
            parsed = _parse_doc_type(result.text)
            if parsed is not None:
                doc_type, confidence = parsed
                return DocTypeIdentifierOutput(
                    doc_type=doc_type,
                    confidence=confidence,
                    signals=[f"LLM:{result.model}"],
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
            signals=["분류 실패, default 강등"],
        )


# --- 파싱 헬퍼 -----------------------------------------------------------


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug or "classified-doc"


def _parse_doc_type(raw: str) -> tuple[DocType, float] | None:
    """LLM JSON 응답 → (DocType, confidence). ko_name 없으면 None."""
    data = _parse_json(raw)
    if not isinstance(data, dict):
        return None
    ko_name = str(data.get("ko_name") or "").strip()
    if not ko_name:
        return None

    domain_raw = str(data.get("domain") or "other").strip()
    domain: Domain = domain_raw if domain_raw in _VALID_DOMAINS else "other"  # type: ignore[assignment]

    doc_id = str(data.get("id") or "").strip()
    if not doc_id or not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", doc_id):
        doc_id = _slugify(doc_id) if doc_id else f"llm-{_slugify(ko_name)[:40]}"

    taxonomy_raw = data.get("taxonomy_path")
    taxonomy = (
        [str(t).strip() for t in taxonomy_raw if str(t).strip()][:5]
        if isinstance(taxonomy_raw, list)
        else []
    )

    try:
        confidence = float(data.get("confidence", 0.7))
    except (TypeError, ValueError):
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))

    doc_type = DocType(
        id=doc_id, ko_name=ko_name, domain=domain, taxonomy_path=taxonomy
    )
    return doc_type, confidence


def _parse_json(text: str) -> dict | list | None:
    text = text.strip()
    fence = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
    return None
