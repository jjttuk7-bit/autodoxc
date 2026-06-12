"""파서 디스패처 — 포맷 감지 + 적절한 파서 호출."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


ParseFormat = Literal["docx", "pdf_text", "hwpx", "hwp", "image", "txt", "unknown"]


@dataclass
class ParseWarning:
    severity: Literal["info", "warning", "error"]
    message: str
    location: str | None = None


@dataclass
class ParsedBlock:
    kind: Literal["heading", "paragraph", "table", "list"]
    text: str
    level: int | None = None


@dataclass
class ParseResult:
    attachment_id: str
    format: ParseFormat
    raw_text: str
    blocks: list[ParsedBlock] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)
    confidence: float = 1.0


def detect_format(path: str | Path) -> ParseFormat:
    p = Path(path)
    suffix = p.suffix.lower()
    mapping: dict[str, ParseFormat] = {
        ".docx": "docx",
        ".pdf": "pdf_text",   # 텍스트 우선, OCR fallback은 B2
        ".hwpx": "hwpx",
        ".hwp": "hwp",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".txt": "txt",
        ".md": "txt",
    }
    return mapping.get(suffix, "unknown")


def parse(path: str | Path, attachment_id: str | None = None) -> ParseResult:
    """포맷 감지 → 해당 파서 호출. B0-5는 docx + pdf_text만 지원."""
    p = Path(path)
    fmt = detect_format(p)
    aid = attachment_id or p.stem

    if fmt == "docx":
        from .docx import parse_docx
        return parse_docx(p, attachment_id=aid)
    if fmt == "pdf_text":
        from .pdf_text import parse_pdf_text
        return parse_pdf_text(p, attachment_id=aid)
    if fmt == "txt":
        text = p.read_text(encoding="utf-8")
        return ParseResult(
            attachment_id=aid,
            format="txt",
            raw_text=text,
            blocks=[ParsedBlock(kind="paragraph", text=text)],
        )

    return ParseResult(
        attachment_id=aid,
        format=fmt,
        raw_text="",
        warnings=[
            ParseWarning(
                severity="error",
                message=f"포맷 {fmt!r} 미지원 — B0-5는 docx/pdf_text/txt만",
            )
        ],
        confidence=0.0,
    )
