from __future__ import annotations

from pydantic import BaseModel, Field

from ..doc import DocType
from ..session import Attachment, Message


class DocTypeIdentifierInput(BaseModel):
    user_input: str
    attachments: list[Attachment] = Field(default_factory=list)
    session_history: list[Message] = Field(default_factory=list)


class DocTypeCandidate(BaseModel):
    doc_type: DocType
    score: float = Field(ge=0.0, le=1.0)


class DocTypeIdentifierOutput(BaseModel):
    doc_type: DocType
    confidence: float = Field(ge=0.0, le=1.0)
    candidates: list[DocTypeCandidate] = Field(default_factory=list)
    signals: list[str] = Field(default_factory=list)
