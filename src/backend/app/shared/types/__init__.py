"""autodoxc 백엔드 단일 진실 소스 타입.

`docs/architecture/06-interfaces.md` §1.1의 모듈 경계를 그대로 따른다.
외부에서는 항상 `from app.shared.types import X`로 import.
"""
from .doc import DocType
from .draft import (
    Draft,
    DraftParagraph,
    DraftSection,
    EmptySlot,
    ParagraphAnnotation,
    ParagraphStatus,
)
from .evidence import Evidence, EvidenceNeed, EvidenceType
from .events import (
    AgentFailedEvent,
    AskUserEvent,
    DraftSectionEvent,
    EditingReadyEvent,
    EvidencesFoundEvent,
    FactsExtractedEvent,
    FillsAppliedEvent,
    ReviewIssueRef,
    ReviewResultEvent,
    SafetyTripEvent,
    SkeletonReadyEvent,
    StreamEvent,
)
from .facts import Fact
from .logic import LogicNode
from .primitives import Domain, Provenance, TextSpan
from .question import Assumption, Question
from .session import Attachment, Message, SessionState
from .skeleton import (
    FieldSpec,
    SkeletonNode,
    SkeletonSource,
    SourceLlmInference,
    SourceOfficialForm,
    SourceRag,
    SourceUserAttached,
    SourceUserLibrary,
)

__all__ = [
    # primitives
    "TextSpan",
    "Provenance",
    "Domain",
    # doc
    "DocType",
    # skeleton
    "FieldSpec",
    "SkeletonNode",
    "SkeletonSource",
    "SourceOfficialForm",
    "SourceUserLibrary",
    "SourceRag",
    "SourceLlmInference",
    "SourceUserAttached",
    # facts
    "Fact",
    # evidence
    "Evidence",
    "EvidenceNeed",
    "EvidenceType",
    # draft
    "Draft",
    "DraftSection",
    "DraftParagraph",
    "ParagraphAnnotation",
    "ParagraphStatus",
    "EmptySlot",
    # logic
    "LogicNode",
    # question
    "Question",
    "Assumption",
    # session
    "SessionState",
    "Attachment",
    "Message",
    # events
    "StreamEvent",
    "SkeletonReadyEvent",
    "FactsExtractedEvent",
    "FillsAppliedEvent",
    "AskUserEvent",
    "EvidencesFoundEvent",
    "DraftSectionEvent",
    "ReviewIssueRef",
    "ReviewResultEvent",
    "EditingReadyEvent",
    "SafetyTripEvent",
    "AgentFailedEvent",
]
