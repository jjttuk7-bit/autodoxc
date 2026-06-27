"""ParseResult → SkeletonNode 추출 테스트."""
from __future__ import annotations

from app.parsers.pipeline import ParsedBlock, ParseResult
from app.parsers.skeleton_extract import skeleton_from_parse


def _result(blocks: list[ParsedBlock]) -> ParseResult:
    return ParseResult(
        attachment_id="att1",
        format="docx",
        raw_text="",
        blocks=blocks,
    )


def test_headings_become_sections_with_user_attached_source() -> None:
    blocks = [
        ParsedBlock(kind="heading", text="신청인 정보", level=1),
        ParsedBlock(kind="paragraph", text="성명, 주소, 연락처를 기재한다."),
        ParsedBlock(kind="heading", text="2. 신청 사유", level=1),
        ParsedBlock(kind="paragraph", text="신청 목적과 배경."),
    ]
    nodes = skeleton_from_parse(_result(blocks), file_id="f123")

    assert len(nodes) == 2
    assert nodes[0].id == "att_sec_1"
    assert nodes[0].source.kind == "user_attached"
    assert nodes[0].source.file_id == "f123"
    # 번호 없는 제목은 "1. " 접두, 있는 제목은 그대로
    assert nodes[0].title == "1. 신청인 정보"
    assert nodes[1].title == "2. 신청 사유"
    # logic_anchor는 본문 첫 줄에서 추정
    assert "성명" in nodes[0].logic_anchor


def test_no_headings_returns_empty_for_fallback() -> None:
    blocks = [
        ParsedBlock(kind="paragraph", text="제목 없는 평문 문서."),
        ParsedBlock(kind="paragraph", text="두 번째 문단."),
    ]
    assert skeleton_from_parse(_result(blocks), file_id="f1") == []


def test_section_cap() -> None:
    blocks = [
        ParsedBlock(kind="heading", text=f"섹션 {i}", level=1)
        for i in range(30)
    ]
    nodes = skeleton_from_parse(_result(blocks), file_id="f1")
    assert len(nodes) == 15  # _MAX_SECTIONS
