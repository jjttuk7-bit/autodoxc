"""에이전트 → 모델 티어 매핑 — ADR 0001 그대로."""
from __future__ import annotations

from typing import Literal


Tier = Literal["opus", "sonnet", "haiku"]
AgentName = Literal[
    "doc_type_identifier",        # #1a
    "skeleton_composer",          # #1b
    "facts_extractor",            # #2
    "gap_analyzer",               # #3
    "logic_architect",            # #4
    "evidence_retriever",         # #5
    "draft_writer",               # #6
    "self_reviewer",              # #7
    "skeleton_learner",           # #8
]


_TIER_MAP: dict[AgentName, Tier] = {
    "doc_type_identifier": "haiku",
    "skeleton_composer": "sonnet",
    "facts_extractor": "sonnet",
    "gap_analyzer": "sonnet",        # 필요 시 opus 승격
    "logic_architect": "opus",
    "evidence_retriever": "haiku",
    "draft_writer": "sonnet",
    "self_reviewer": "opus",
    "skeleton_learner": "sonnet",
}


def tier_for_agent(agent: AgentName) -> Tier:
    return _TIER_MAP[agent]
