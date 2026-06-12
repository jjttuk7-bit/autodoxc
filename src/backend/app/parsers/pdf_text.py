"""PDF 텍스트 레이어 파서 — pypdf 기반.

스캔본 PDF는 텍스트 레이어가 없거나 비어있어 confidence가 낮게 잡힌다.
OCR 폴백은 B2에서 추가.
"""
from __future__ import annotations

from pathlib import Path

from .pipeline import ParsedBlock, ParseResult, ParseWarning


def parse_pdf_text(path: Path, *, attachment_id: str) -> ParseResult:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        return ParseResult(
            attachment_id=attachment_id,
            format="pdf_text",
            raw_text="",
            warnings=[ParseWarning(severity="error", message=f"pypdf 미설치: {e!s}")],
            confidence=0.0,
        )

    try:
        reader = PdfReader(str(path))
    except Exception as e:
        return ParseResult(
            attachment_id=attachment_id,
            format="pdf_text",
            raw_text="",
            warnings=[
                ParseWarning(severity="error", message=f"PDF 열기 실패: {type(e).__name__}")
            ],
            confidence=0.0,
        )

    if reader.is_encrypted:
        return ParseResult(
            attachment_id=attachment_id,
            format="pdf_text",
            raw_text="",
            warnings=[
                ParseWarning(
                    severity="error",
                    message="암호화된 PDF — 평문 변환 후 다시 시도하세요",
                )
            ],
            confidence=0.0,
        )

    blocks: list[ParsedBlock] = []
    full_text_parts: list[str] = []

    for page_idx, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text = text.strip()
        if text:
            blocks.append(ParsedBlock(kind="paragraph", text=text))
            full_text_parts.append(text)

    raw_text = "\n\n".join(full_text_parts)
    # 페이지가 있는데 추출 텍스트가 짧으면 스캔본 의심
    if reader.pages and len(raw_text) < 50:
        return ParseResult(
            attachment_id=attachment_id,
            format="pdf_text",
            raw_text=raw_text,
            blocks=blocks,
            warnings=[
                ParseWarning(
                    severity="warning",
                    message="텍스트 추출이 거의 없음 — 스캔본일 수 있음. OCR 폴백은 B2 단계에서 지원.",
                )
            ],
            confidence=0.3,
        )

    return ParseResult(
        attachment_id=attachment_id,
        format="pdf_text",
        raw_text=raw_text,
        blocks=blocks,
        confidence=0.85,
    )
