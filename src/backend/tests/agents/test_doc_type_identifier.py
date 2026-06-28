"""#1a DocTypeIdentifier — 키워드 빠른 경로 + LLM 구조화 분류 파싱."""
from __future__ import annotations

import pytest

from app.agents.doc_type_identifier import DocTypeIdentifier, _parse_doc_type
from app.llm.adapter import DummyLLMClient, LLMResult
from app.shared.types.agents.doc_type_identifier import DocTypeIdentifierInput


def test_parse_valid_classification() -> None:
    raw = (
        '{"id":"business-registration","ko_name":"사업자등록 신청서",'
        '"domain":"permit","taxonomy_path":["인허가","세무"],"confidence":0.82}'
    )
    parsed = _parse_doc_type(raw)
    assert parsed is not None
    dt, conf = parsed
    assert dt.id == "business-registration"
    assert dt.ko_name == "사업자등록 신청서"
    assert dt.domain == "permit"
    assert dt.taxonomy_path == ["인허가", "세무"]
    assert conf == 0.82


def test_parse_invalid_domain_falls_back_to_other() -> None:
    parsed = _parse_doc_type('{"ko_name":"무언가","domain":"unknown"}')
    assert parsed is not None
    assert parsed[0].domain == "other"


def test_parse_bad_id_is_slugified() -> None:
    parsed = _parse_doc_type('{"id":"사업자 등록","ko_name":"사업자등록 신청서"}')
    assert parsed is not None
    # 비-ascii id는 음차 대신 ko_name 기반 llm- 접두 슬러그
    assert parsed[0].id.startswith("llm-") or parsed[0].id.isascii()


def test_parse_empty_ko_name_returns_none() -> None:
    assert _parse_doc_type('{"ko_name":""}') is None
    assert _parse_doc_type("{}") is None
    assert _parse_doc_type("not json") is None


def test_confidence_clamped() -> None:
    parsed = _parse_doc_type('{"ko_name":"x","confidence":9.0}')
    assert parsed is not None and parsed[1] == 1.0


@pytest.mark.asyncio
async def test_keyword_fast_path_skips_llm() -> None:
    # dummy LLM이라도 키워드가 있으면 시드 매칭 (LLM 호출 전)
    agent = DocTypeIdentifier(DummyLLMClient(lambda s, u, t: "{}"))
    out = await agent.run(DocTypeIdentifierInput(user_input="외국인 고용 계획서"))
    assert out.doc_type.id == "foreign-worker-employment-plan"
    assert out.confidence >= 0.9


@pytest.mark.asyncio
async def test_dummy_unknown_falls_back_to_default() -> None:
    # 시드 키워드 없는 입력 + dummy run_json "{}" → 분류 실패 → default 강등
    agent = DocTypeIdentifier(DummyLLMClient(lambda s, u, t: "{}"))
    out = await agent.run(DocTypeIdentifierInput(user_input="사내 공지문 작성해줘"))
    assert out.doc_type.id == "generic-administrative-doc"
    assert out.confidence <= 0.3


@pytest.mark.asyncio
async def test_data_seed_keyword_intercepts() -> None:
    # 데이터 시드 키워드는 LLM 전에 가로채 해당 시드 doc_type 반환
    agent = DocTypeIdentifier(DummyLLMClient(lambda s, u, t: "{}"))
    out1 = await agent.run(DocTypeIdentifierInput(user_input="사업자등록 신청서 써줘"))
    assert out1.doc_type.id == "business-registration"
    out2 = await agent.run(DocTypeIdentifierInput(user_input="정보공개 청구하려고"))
    assert out2.doc_type.id == "information-disclosure-request"


@pytest.mark.asyncio
async def test_specific_seed_keyword_beats_legacy() -> None:
    # "행정심판 답변"(시드)이 레거시 "행정심판"(청구서)보다 우선
    agent = DocTypeIdentifier(DummyLLMClient(lambda s, u, t: "{}"))
    ans = await agent.run(DocTypeIdentifierInput(user_input="행정심판 답변서 작성"))
    assert ans.doc_type.id == "administrative-appeal-response"
    # 단순 "행정심판 청구서"는 레거시 청구서로
    claim = await agent.run(DocTypeIdentifierInput(user_input="행정심판 청구서 써줘"))
    assert claim.doc_type.id == "administrative-appeal"


@pytest.mark.asyncio
async def test_llm_classification_used_when_returned() -> None:
    raw = '{"id":"business-registration","ko_name":"사업자등록 신청서","domain":"permit","confidence":0.8}'

    class _FakeLLM:
        async def run_text(self, **kw) -> LLMResult:  # noqa: D401
            return LLMResult(text=raw, input_tokens=1, output_tokens=1, model="fake")

        async def run_json(self, **kw) -> LLMResult:
            return LLMResult(text=raw, input_tokens=1, output_tokens=1, model="fake")

    agent = DocTypeIdentifier(_FakeLLM())  # type: ignore[arg-type]
    # 시드 키워드 없는 입력 → LLM 분류 경로로 진입
    out = await agent.run(DocTypeIdentifierInput(user_input="이 문서 좀 만들어줘"))
    assert out.doc_type.id == "business-registration"
    assert out.doc_type.domain == "permit"
    assert out.confidence == 0.8
