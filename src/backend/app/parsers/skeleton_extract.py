"""ParseResult → SkeletonNode[] — 첨부 양식의 제목 구조에서 골격 추출.

DA4(첨부 양식 파서)의 출력(`ParseResult.blocks`)을 받아, heading 블록을 섹션 경계로
삼아 골격을 만든다. 골격 소스는 `user_attached`(우선순위 최상위, 01-agents.md §결정).

heading이 하나도 없으면 구조를 추출할 수 없다고 보고 빈 리스트 반환 →
호출자가 일반 SkeletonComposer로 폴백.
"""
from __future__ import annotations

from app.shared.types import SkeletonNode, SourceUserAttached

from .pipeline import ParsedBlock, ParseResult


_MAX_SECTIONS = 15
_ANCHOR_MAX_LEN = 60


def _anchor_from_content(blocks: list[ParsedBlock]) -> str:
    """섹션 본문 첫 줄에서 logic_anchor 추정."""
    for b in blocks:
        text = b.text.strip()
        if text:
            snippet = text.splitlines()[0].strip()
            if len(snippet) > _ANCHOR_MAX_LEN:
                snippet = snippet[:_ANCHOR_MAX_LEN].rstrip() + "…"
            return snippet
    return ""


def skeleton_from_parse(
    result: ParseResult, *, file_id: str
) -> list[SkeletonNode]:
    """첨부 양식의 heading 구조 → SkeletonNode 목록 (source=user_attached).

    heading이 없으면 빈 리스트 (구조 추출 불가 → 일반 골격 구성기로 폴백).
    """
    source = SourceUserAttached(file_id=file_id)

    # heading 인덱스 수집
    heading_idxs = [
        i for i, b in enumerate(result.blocks) if b.kind == "heading"
    ]
    if not heading_idxs:
        return []

    nodes: list[SkeletonNode] = []
    for n, h_idx in enumerate(heading_idxs[:_MAX_SECTIONS], start=1):
        heading = result.blocks[h_idx]
        # 이 heading 다음 ~ 다음 heading 전까지의 본문 블록
        next_h = (
            heading_idxs[n] if n < len(heading_idxs) else len(result.blocks)
        )
        content = result.blocks[h_idx + 1 : next_h]

        title = heading.text.strip()
        # 번호가 없으면 "n. " 접두
        if not title[:2].strip().rstrip(".").isdigit():
            title = f"{n}. {title}"

        anchor = _anchor_from_content(content)
        nodes.append(
            SkeletonNode(
                id=f"att_sec_{n}",
                title=title,
                role="첨부 양식에서 추출한 섹션",
                logic_anchor=anchor or f"'{heading.text.strip()}' 섹션의 내용은?",
                source=source,
            )
        )

    return nodes
