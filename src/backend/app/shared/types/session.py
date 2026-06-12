"""SessionState — 모든 런타임 상태의 컨테이너."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .doc import DocType
from .draft import Draft, EmptySlot
from .evidence import Evidence
from .facts import Fact
from .logic import LogicNode
from .question import Assumption, Question
from .skeleton import SkeletonNode


class Attachment(BaseModel):
    id: str
    file_name: str
    format: str
    storage_uri: str
    sha256: str | None = None


class Message(BaseModel):
    id: str
    role: str  # "user" | "system" | "agent:<name>"
    text: str
    created_at: datetime


class SessionState(BaseModel):
    session_id: str
    doc_type: DocType | None = None
    skeleton: list[SkeletonNode] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    fills: list[Fact] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    logic_tree: list[LogicNode] = Field(default_factory=list)
    evidences: list[Evidence] = Field(default_factory=list)
    draft: Draft | None = None
    empty_slots: list[EmptySlot] = Field(default_factory=list)
    pending_questions: list[Question] = Field(default_factory=list)
    user_input_history: list[Message] = Field(default_factory=list)
    user_attachments: list[Attachment] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
