"""문서 청킹 — 구조 우선 + 슬라이딩 윈도우 폴백.

02-data-assets §DA3:
- 구조 명확(섹션·문단 경계) → 그 단위
- 약함 → 슬라이딩 윈도우 (window=400, stride=300)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    start: int
    end: int
    section_id: str | None = None


def _approx_tokens(text: str) -> int:
    # 한국어는 byte 기반보다 character 기반이 안전 — 매우 거친 추정
    return max(1, len(text) // 2)


def split_by_paragraphs(
    text: str,
    *,
    max_tokens: int = 500,
    section_hints: list[tuple[int, str]] | None = None,
) -> list[Chunk]:
    """문단 경계 우선. 한 문단이 max_tokens 초과 시 슬라이딩 윈도우 폴백.

    section_hints: [(char_offset, section_id), ...] — 청크에 section_id 부착.
    """
    if not text.strip():
        return []

    paragraphs = _split_paragraphs(text)
    chunks: list[Chunk] = []
    cursor = 0
    section_iter = iter(sorted(section_hints or []))
    current_section: str | None = None
    next_hint = next(section_iter, None)

    for para in paragraphs:
        start = text.find(para, cursor)
        end = start + len(para)
        cursor = end

        # section 매핑
        while next_hint is not None and next_hint[0] <= start:
            current_section = next_hint[1]
            next_hint = next(section_iter, None)

        if _approx_tokens(para) <= max_tokens:
            chunks.append(
                Chunk(text=para, start=start, end=end, section_id=current_section)
            )
        else:
            # 슬라이딩 윈도우 폴백
            chunks.extend(
                _sliding(
                    para,
                    base_offset=start,
                    section_id=current_section,
                    window=max_tokens,
                    stride=max_tokens - 100,
                )
            )

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n")]
    return [p for p in parts if p]


def _sliding(
    text: str,
    *,
    base_offset: int,
    section_id: str | None,
    window: int,
    stride: int,
) -> list[Chunk]:
    chars_per_window = window * 2  # _approx_tokens 역산
    chars_stride = stride * 2
    out: list[Chunk] = []
    i = 0
    while i < len(text):
        piece = text[i : i + chars_per_window]
        if not piece.strip():
            break
        out.append(
            Chunk(
                text=piece,
                start=base_offset + i,
                end=base_offset + i + len(piece),
                section_id=section_id,
            )
        )
        if i + chars_per_window >= len(text):
            break
        i += chars_stride
    return out
