from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..doc import DocType
from ..draft import Draft, EmptySlot
from ..evidence import Evidence
from ..facts import Fact
from ..logic import LogicNode
from ..question import Assumption
from ..skeleton import SkeletonNode


class StyleOptions(BaseModel):
    formality: Literal["formal", "neutral"] | None = None
    length: Literal["concise", "standard", "detailed"] | None = None


class DraftWriterInput(BaseModel):
    skeleton: list[SkeletonNode]
    facts: list[Fact]
    fills: list[Fact] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    logic_tree: list[LogicNode] = Field(default_factory=list)
    evidences: list[Evidence] = Field(default_factory=list)
    style: StyleOptions | None = None
    target_sections: list[str] | None = None  # 부분 재작성 (04 §3)
    doc_type: DocType | None = None  # 본문 시드 분기용


class DraftWriterOutput(BaseModel):
    draft: Draft
    empty_slots: list[EmptySlot] = Field(default_factory=list)
