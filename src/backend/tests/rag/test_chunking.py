"""청킹 — 문단 경계 우선 + 슬라이딩 윈도우 폴백."""
from __future__ import annotations

from app.data.rag.chunking import split_by_paragraphs


def test_empty_text() -> None:
    assert split_by_paragraphs("") == []
    assert split_by_paragraphs("   \n\n  ") == []


def test_paragraph_split() -> None:
    text = "첫째 문단.\n\n둘째 문단.\n\n셋째 문단."
    chunks = split_by_paragraphs(text)
    assert len(chunks) == 3
    assert chunks[0].text == "첫째 문단."
    assert chunks[1].text == "둘째 문단."
    assert chunks[2].text == "셋째 문단."


def test_section_hints() -> None:
    text = "intro 문장.\n\n섹션 1 본문.\n\n섹션 2 본문."
    hints = [(0, "sec_0"), (text.find("섹션 1"), "sec_1"), (text.find("섹션 2"), "sec_2")]
    chunks = split_by_paragraphs(text, section_hints=hints)
    assert chunks[0].section_id == "sec_0"
    assert chunks[1].section_id == "sec_1"
    assert chunks[2].section_id == "sec_2"


def test_long_paragraph_sliding() -> None:
    para = "긴 문장이 반복됩니다 " * 200  # 약 3000 chars
    chunks = split_by_paragraphs(para, max_tokens=200)
    assert len(chunks) >= 2
    # 윈도우 간 겹침이 있어야 함
    for i in range(1, len(chunks)):
        assert chunks[i].start < chunks[i - 1].end
