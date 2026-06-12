"""DA4 첨부 양식 파서 — 단계적 폴백 체인 (ADR 0006).

B0-5 1단계: .docx + .pdf (텍스트 레이어).
B2에서 .hwpx, .hwp, .pdf(OCR), 이미지 추가.
"""
from .docx import parse_docx
from .pdf_text import parse_pdf_text
from .pipeline import ParseResult, ParseWarning, parse

__all__ = ["parse", "parse_docx", "parse_pdf_text", "ParseResult", "ParseWarning"]
