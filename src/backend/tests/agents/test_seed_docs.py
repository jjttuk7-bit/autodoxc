"""데이터 기반 시드 레지스트리 — 골격·렌더·치환·영향섹션."""
from __future__ import annotations

from app.agents.seed_docs import (
    SEED_DOCS,
    doc_type_by_keyword,
    field_to_section_map,
    is_data_seed,
    render_section,
    seed_skeleton_nodes,
)


def test_registry_has_seeds() -> None:
    assert "information-disclosure-request" in SEED_DOCS
    assert "business-registration" in SEED_DOCS
    assert is_data_seed("business-registration")
    assert not is_data_seed("administrative-appeal")  # 레거시 시드
    assert not is_data_seed("unknown-doc")


def test_keyword_lookup() -> None:
    assert doc_type_by_keyword("정보공개 청구").id == "information-disclosure-request"
    assert doc_type_by_keyword("사업자등록 하려고").id == "business-registration"
    assert doc_type_by_keyword("아무 관련 없는 말") is None


def test_skeleton_nodes_official_form_source() -> None:
    nodes = seed_skeleton_nodes("information-disclosure-request")
    assert len(nodes) == 5
    assert nodes[0].source.kind == "official_form"
    assert nodes[0].title.startswith("1.")


def test_render_empty_without_facts() -> None:
    sec = render_section("business-registration", "sec_1", {})
    assert sec is not None
    # facts 없으면 자리표시자 유지 + empty
    assert any("[[" in p.text for p in sec.paragraphs)
    assert all(
        p.annotations.status == "empty" for p in sec.paragraphs if "[[" in p.text
    )


def test_render_interpolates_facts_to_confirmed() -> None:
    facts = {"trade_name": "테스트상사", "owner_name": "홍길동"}
    sec = render_section("business-registration", "sec_1", facts)
    assert sec is not None
    texts = "\n".join(p.text for p in sec.paragraphs)
    assert "테스트상사" in texts and "홍길동" in texts
    # 치환된 문단은 confirmed로 승격
    confirmed = [p for p in sec.paragraphs if "테스트상사" in p.text]
    assert confirmed and confirmed[0].annotations.status == "confirmed"


def test_evidence_backed_preserved() -> None:
    sec = render_section("business-registration", "sec_4", {})
    assert sec is not None
    ev = [p for p in sec.paragraphs if p.annotations.status == "evidence_backed"]
    assert ev and "ev_vat_8" in ev[0].annotations.evidence_refs


def test_field_to_section_map() -> None:
    m = field_to_section_map("business-registration")
    assert m["trade_name"] == ["sec_1"]
    assert m["open_date"] == ["sec_4"]
