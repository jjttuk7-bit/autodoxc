from __future__ import annotations

from pydantic import BaseModel, Field

from ..facts import Fact
from ..session import Attachment, Message
from ..skeleton import FieldSpec, SkeletonNode


class FactsExtractorInput(BaseModel):
    user_input_history: list[Message]
    skeleton: list[SkeletonNode]
    attachments: list[Attachment] = Field(default_factory=list)


class InferredSignal(BaseModel):
    fact: Fact
    needs_confirmation: bool


class FactsExtractorOutput(BaseModel):
    facts: list[Fact]
    unresolved_fields: list[FieldSpec] = Field(default_factory=list)
    inferred_signals: list[InferredSignal] = Field(default_factory=list)
