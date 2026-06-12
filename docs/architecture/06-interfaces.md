# 06. 인터페이스 직역 계획 (B0-1)

> **작성**: lead-architect 역할
> **목적**: `01-agents.md`의 TypeScript 의사코드를 **Pydantic v2 모델**로 1:1 직역하는 매핑, 모듈 경계, 프론트엔드 타입 자동 동기화 절차.
> **단일 진실 소스**: `src/backend/app/shared/types/`의 Pydantic 모델. 프론트는 여기서 OpenAPI를 거쳐 자동 생성된 TypeScript만 사용.
> **walking skeleton과의 관계**: walking skeleton(`app/shared/types.py`)에 있는 부분 직역은 본 명세대로 확장 + 디렉토리 분할로 교체.

---

## 0. 직역 원칙

| 원칙 | 적용 |
|---|---|
| **단일 진실 소스** | Pydantic 모델만이 진실. TS 타입은 생성물 — 손으로 안 씀 |
| **불변 식별자** | 모든 도메인 엔티티에 `id: str` 필수 (UUID v7 또는 도메인 고유 kebab-case) |
| **Discriminated Union** | TS의 `{ kind: "X"; ... } | { kind: "Y"; ... }`를 `Field(discriminator="kind")`로 직역 |
| **Optional vs None** | TS의 `T | undefined`/`T?`는 Pydantic `T | None = None` |
| **불변 컬렉션** | 기본은 `list[T]` (변경 가능) — immutability 필요한 곳만 `tuple` |
| **JSON 직렬화 가능** | 모든 모델은 `model_dump_json()` 가능 — datetime은 ISO 문자열, Enum은 값 |
| **버전드 enum** | Literal[...] 위주 (Enum 클래스보다 직렬화 단순) |
| **불필요한 nullable 금지** | TS에서 옵셔널이지만 항상 채워지는 필드는 Pydantic에서 required로 강화 |

### 직역 규약 표

| TypeScript 의사코드 | Pydantic v2 |
|---|---|
| `type X = { a: string; b: number }` | `class X(BaseModel): a: str; b: float` |
| `string | undefined` | `str | None = None` |
| `Literal<"a" | "b">` | `Literal["a", "b"]` |
| `T[]` | `list[T]` (default factory 필요 시 `Field(default_factory=list)`) |
| `Record<K, V>` | `dict[K, V]` |
| `{ kind: "a" } | { kind: "b" }` | `Annotated[Union[A, B], Field(discriminator="kind")]` |
| TS lambda 콜백 | 모델 외부 인터페이스(함수 시그니처)로 분리 — Pydantic 모델 안에 두지 않음 |
| `timestamp` (TS의 ISO 문자열) | `datetime` (Pydantic이 ISO 자동 직렬화) |
| `unknown` / `any` | `JsonValue` 또는 `Any` (지양) |

---

## 1. 모듈 경계

### 1.1 디렉토리 구조

```
src/backend/app/shared/types/
├── __init__.py             # 모든 모델 re-export (외부에서 단일 import)
├── primitives.py           # TextSpan, Provenance, 공통 enum/literal
├── doc.py                  # DocType, 분류 taxonomy
├── skeleton.py             # SkeletonNode, FieldSpec, SkeletonSource (discriminated)
├── facts.py                # Fact (source별 분기는 source 필드)
├── evidence.py             # Evidence, EvidenceNeed
├── draft.py                # DraftSection, DraftParagraph, ParagraphAnnotation, EmptySlot
├── logic.py                # LogicNode
├── question.py             # Question, Assumption
├── session.py              # SessionState (위 모든 것의 컨테이너)
├── agents/                 # 에이전트별 Input/Output 모델
│   ├── __init__.py
│   ├── doc_type_identifier.py
│   ├── skeleton_composer.py
│   ├── facts_extractor.py
│   ├── gap_analyzer.py
│   ├── logic_architect.py
│   ├── evidence_retriever.py
│   ├── draft_writer.py
│   ├── self_reviewer.py
│   └── skeleton_learner.py
├── events/                 # SSE 페이로드
│   ├── __init__.py
│   └── stream.py           # discriminated union of all stream events
└── external/               # 외부 API I/O
    ├── __init__.py
    ├── law.py
    ├── stat.py
    └── precedent.py
```

### 1.2 import 규약

- 다른 모듈에서는 항상 `from app.shared.types import X` (단일 진입점)
- `app.shared.types.__init__.py`가 명시 re-export 목록 관리 — 새 모델 추가 시 명시 등록
- 순환 import 방지: `agents/X.py`는 `app.shared.types` 만 import, 다른 `agents/Y.py`는 import 안 함 (필요 시 공통 모델로 추출)

### 1.3 운영 규약

- `shared/types/` 수정은 **lead-architect 단독 권한**. 다른 멤버는 변경 제안 → `references/interface-change-protocol.md` 적용
- 모델 변경 시 OpenAPI 재생성 → 프론트 타입 재생성 → CI 회귀 (자동화 절차 §6)

---

## 2. 공통 데이터 타입 직역

### 2.1 primitives.py

```python
from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class TextSpan(BaseModel):
    """사용자 입력 텍스트의 위치 — UI 하이라이트용."""
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    source_message_id: str | None = None


class Provenance(BaseModel):
    source_url: str | None = None
    fetched_at: datetime
    fetched_by: Literal["crawler", "manual", "user_contribution"]
    license: Literal["public_domain", "kogl_type1", "other"] = "other"
    notes: str | None = None


# 도메인 분류 — 다른 모듈에서 공용
Domain = Literal["dispute", "permit", "internal", "other"]
```

### 2.2 doc.py — `DocType`

```python
from pydantic import BaseModel, Field
from .primitives import Domain


class DocType(BaseModel):
    id: str  # canonical kebab-case
    ko_name: str
    domain: Domain = "other"
    taxonomy_path: list[str] = Field(default_factory=list)
```

### 2.3 skeleton.py — `SkeletonNode` + `FieldSpec` + `SkeletonSource`

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field


class FieldSpec(BaseModel):
    field_id: str
    label: str
    type: Literal["text", "number", "date", "money", "duration", "enum"]
    hint: str | None = None
    example: str | None = None
    fill_strategy: Literal["ask_user", "infer", "rag", "default"]


# --- SkeletonSource (discriminated union) -----------------------------------


class _SourceBase(BaseModel):
    kind: str


class SourceOfficialForm(_SourceBase):
    kind: Literal["official_form"] = "official_form"
    form_id: str
    agency: str


class SourceUserLibrary(_SourceBase):
    kind: Literal["user_library"] = "user_library"
    entry_id: str
    usage_count: int = Field(ge=0)


class SourceRag(_SourceBase):
    kind: Literal["rag"] = "rag"
    sample_ids: list[str] = Field(default_factory=list)


class SourceLlmInference(_SourceBase):
    kind: Literal["llm_inference"] = "llm_inference"
    confidence: float = Field(ge=0.0, le=1.0)


class SourceUserAttached(_SourceBase):
    kind: Literal["user_attached"] = "user_attached"
    file_id: str


SkeletonSource = Annotated[
    Union[
        SourceOfficialForm,
        SourceUserLibrary,
        SourceRag,
        SourceLlmInference,
        SourceUserAttached,
    ],
    Field(discriminator="kind"),
]


class SkeletonNode(BaseModel):
    id: str
    title: str
    role: str
    logic_anchor: str
    required_fields: list[FieldSpec] = Field(default_factory=list)
    optional_fields: list[FieldSpec] = Field(default_factory=list)
    children: list["SkeletonNode"] = Field(default_factory=list)
    source: SkeletonSource


SkeletonNode.model_rebuild()  # 재귀 forward ref 해결
```

### 2.4 facts.py — `Fact`

```python
from typing import Any, Literal
from pydantic import BaseModel, Field
from .primitives import TextSpan


class Fact(BaseModel):
    field_id: str
    value: Any  # 검증은 FieldSpec.type과 함께 도메인 레이어에서
    source: Literal["explicit", "inferred", "defaulted", "rag"]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_span: TextSpan | None = None
    rationale: str | None = None
```

### 2.5 evidence.py — `Evidence` + `EvidenceNeed`

```python
from typing import Literal
from pydantic import BaseModel, Field


EvidenceType = Literal[
    "statute", "precedent", "statistic", "similar_doc", "convention"
]


class Evidence(BaseModel):
    id: str
    type: EvidenceType
    citation: str
    source_url: str | None = None
    snippet: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    applied_to: list[str] = Field(default_factory=list)  # logic node ids


class EvidenceNeed(BaseModel):
    id: str
    type: EvidenceType
    query: str
    must_have: bool = False
```

### 2.6 draft.py — `DraftParagraph` + `DraftSection` + `EmptySlot`

```python
from typing import Literal
from pydantic import BaseModel, Field


ParagraphStatus = Literal[
    "confirmed", "inferred", "defaulted", "empty", "evidence_backed"
]


class ParagraphAnnotation(BaseModel):
    status: ParagraphStatus
    fact_refs: list[str] = Field(default_factory=list)
    assumption_refs: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    needs_user_input: bool = False


class DraftParagraph(BaseModel):
    text: str
    annotations: ParagraphAnnotation


class DraftSection(BaseModel):
    skeleton_id: str
    title: str
    paragraphs: list[DraftParagraph] = Field(default_factory=list)


class Draft(BaseModel):
    sections: list[DraftSection] = Field(default_factory=list)


class EmptySlot(BaseModel):
    section_id: str
    field_id: str
    placeholder_text: str
    why_empty: Literal["no_data", "user_declined", "low_confidence"]
```

### 2.7 logic.py — `LogicNode`

```python
from pydantic import BaseModel, Field
from .evidence import EvidenceNeed


class LogicNode(BaseModel):
    id: str
    section_id: str
    claim: str
    sub_claims: list["LogicNode"] = Field(default_factory=list)
    depends_on_facts: list[str] = Field(default_factory=list)
    evidence_needs: list[EvidenceNeed] = Field(default_factory=list)
    conflict: bool = False


LogicNode.model_rebuild()
```

### 2.8 question.py

```python
from pydantic import BaseModel, Field
from typing import Any


class Question(BaseModel):
    field_ids: list[str]
    prompt: str
    why: str
    examples: list[str] = Field(default_factory=list)


class Assumption(BaseModel):
    field_id: str
    assumed_value: Any
    rationale: str
    editable: bool = True
```

### 2.9 session.py — `SessionState`

```python
from datetime import datetime
from pydantic import BaseModel, Field

from .doc import DocType
from .skeleton import SkeletonNode
from .facts import Fact
from .question import Question, Assumption
from .draft import Draft, EmptySlot
from .logic import LogicNode
from .evidence import Evidence


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
```

---

## 3. 에이전트별 I/O 직역

각 에이전트의 Input/Output을 별도 모델로. 에이전트 함수 시그니처는 다음 표준:

```python
async def run(input: AgentXInput) -> AgentXOutput: ...
```

### 3.1 `agents/doc_type_identifier.py`

```python
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
```

### 3.2 `agents/skeleton_composer.py`

```python
from pydantic import BaseModel, Field
from ..doc import DocType
from ..skeleton import SkeletonNode, SkeletonSource
from ..session import Attachment


class UserContext(BaseModel):
    industry: str | None = None
    target_agency: str | None = None
    purpose: str | None = None


class SkeletonComposerInput(BaseModel):
    doc_type: DocType
    attachments: list[Attachment] = Field(default_factory=list)
    user_context: UserContext | None = None


class CompositionMeta(BaseModel):
    primary_source: SkeletonSource
    contributions: list[dict]  # {source, sections}
    conflicts_resolved: list[dict] = Field(default_factory=list)


class SkeletonComposerOutput(BaseModel):
    skeleton: list[SkeletonNode]
    composition_meta: CompositionMeta
```

### 3.3 `agents/facts_extractor.py`

```python
from pydantic import BaseModel, Field
from ..skeleton import SkeletonNode, FieldSpec
from ..facts import Fact
from ..session import Attachment, Message


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
```

### 3.4 `agents/gap_analyzer.py`

```python
from pydantic import BaseModel, Field
from ..skeleton import SkeletonNode
from ..facts import Fact
from ..question import Question, Assumption
from ..evidence import EvidenceNeed
from ..doc import DocType
from .facts_extractor import InferredSignal


class GapAnalyzerInput(BaseModel):
    skeleton: list[SkeletonNode]
    facts: list[Fact]
    unresolved_fields: list  # FieldSpec[]
    inferred_signals: list[InferredSignal] = Field(default_factory=list)
    doc_type: DocType
    attempt_count: int = 0
    rag_results: list = Field(default_factory=list)  # Evidence[] (2-pass)


class GapAnalyzerOutput(BaseModel):
    fills: list[Fact] = Field(default_factory=list)
    fills_pending_rag: list[EvidenceNeed] = Field(default_factory=list)
    next_question: Question | None = None
    assumptions: list[Assumption] = Field(default_factory=list)
    ready_to_draft: bool = False
```

### 3.5 `agents/logic_architect.py`

```python
from pydantic import BaseModel
from ..doc import DocType
from ..skeleton import SkeletonNode
from ..facts import Fact
from ..logic import LogicNode
from ..evidence import EvidenceNeed


class LogicArchitectInput(BaseModel):
    doc_type: DocType
    skeleton: list[SkeletonNode]
    facts: list[Fact]


class LogicArchitectOutput(BaseModel):
    logic_tree: list[LogicNode]
    evidence_needs: list[EvidenceNeed]
```

### 3.6 `agents/evidence_retriever.py`

```python
from pydantic import BaseModel, Field
from ..evidence import Evidence, EvidenceNeed
from ..doc import DocType
from ..primitives import Domain


class EvidenceRetrieverInput(BaseModel):
    needs: list[EvidenceNeed]
    doc_type: DocType
    domain: Domain
    max_per_need: int = 3


class EvidenceRetrieverOutput(BaseModel):
    evidences: list[Evidence] = Field(default_factory=list)
    unmet_needs: list[EvidenceNeed] = Field(default_factory=list)
```

### 3.7 `agents/draft_writer.py`

```python
from typing import Literal
from pydantic import BaseModel, Field
from ..skeleton import SkeletonNode
from ..facts import Fact
from ..question import Assumption
from ..logic import LogicNode
from ..evidence import Evidence
from ..draft import Draft, EmptySlot


class StyleOptions(BaseModel):
    formality: Literal["formal", "neutral"] | None = None
    length: Literal["concise", "standard", "detailed"] | None = None


class DraftWriterInput(BaseModel):
    skeleton: list[SkeletonNode]
    facts: list[Fact]
    fills: list[Fact] = Field(default_factory=list)
    assumptions: list[Assumption] = Field(default_factory=list)
    logic_tree: list[LogicNode]
    evidences: list[Evidence] = Field(default_factory=list)
    style: StyleOptions | None = None
    target_sections: list[str] | None = None  # 부분 재작성용 (04 §3)


class DraftWriterOutput(BaseModel):
    draft: Draft
    empty_slots: list[EmptySlot] = Field(default_factory=list)
```

> 스트리밍 산출은 `AsyncIterator[DraftSection]` — 모델 외부 인터페이스로 정의 (Pydantic 모델 안에 두지 않음).

### 3.8 `agents/self_reviewer.py`

```python
from typing import Literal
from pydantic import BaseModel, Field
from ..draft import Draft
from ..logic import LogicNode
from ..evidence import Evidence
from ..facts import Fact
from ..skeleton import SkeletonNode


class IssueLocation(BaseModel):
    section_id: str
    paragraph_idx: int | None = None


class ReviewIssue(BaseModel):
    severity: Literal["blocker", "warning", "info"]
    type: Literal[
        "logic_gap", "fact_mismatch", "tone",
        "missing_evidence", "redundancy", "format"
    ]
    location: IssueLocation
    description: str
    suggestion: str | None = None


class SelfReviewerInput(BaseModel):
    draft: Draft
    logic_tree: list[LogicNode]
    evidences: list[Evidence] = Field(default_factory=list)
    facts: list[Fact]
    skeleton: list[SkeletonNode]
    review_round: int = Field(ge=1, le=2)


class SelfReviewerOutput(BaseModel):
    passed: bool
    issues: list[ReviewIssue] = Field(default_factory=list)
    must_fix: bool = False
```

### 3.9 `agents/skeleton_learner.py` (#8)

```python
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from ..doc import DocType
from ..skeleton import SkeletonNode
from ..draft import Draft


class UserEdit(BaseModel):
    type: Literal["add_section", "remove_section", "rename", "reorder", "edit_text"]
    target: dict  # {section_id?, new_position?}
    before: str | None = None
    after: str | None = None


class SkeletonLearnerInput(BaseModel):
    session_id: str
    doc_type: DocType
    original_skeleton: list[SkeletonNode]
    final_draft: Draft
    user_edits: list[UserEdit] = Field(default_factory=list)
    confirmed_at: datetime


class SkeletonLearnerOutput(BaseModel):
    library_entry_id: str
    promoted_to_shared: bool = False
    diff_summary: str
```

---

## 4. SSE 이벤트 페이로드 직역

`events/stream.py` — 백엔드가 SSE로 발산하는 모든 이벤트의 discriminated union.

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field
from .doc import DocType
from .skeleton import SkeletonNode
from .draft import DraftSection
from .question import Question, Assumption
from .evidence import Evidence
from .agents.self_reviewer import ReviewIssue


# --- 개별 이벤트 -----------------------------------------------------------


class SkeletonReadyEvent(BaseModel):
    kind: Literal["skeleton_ready"] = "skeleton_ready"
    doc_type: DocType
    skeleton: list[SkeletonNode]


class FactsExtractedEvent(BaseModel):
    kind: Literal["facts_extracted"] = "facts_extracted"
    fact_count: int
    unresolved_count: int


class FillsAppliedEvent(BaseModel):
    kind: Literal["fills_applied"] = "fills_applied"
    fills_count: int
    assumptions: list[Assumption] = Field(default_factory=list)


class AskUserEvent(BaseModel):
    kind: Literal["ask_user"] = "ask_user"
    question: Question


class EvidencesFoundEvent(BaseModel):
    kind: Literal["evidences_found"] = "evidences_found"
    evidences: list[Evidence]


class DraftSectionEvent(BaseModel):
    kind: Literal["draft_section"] = "draft_section"
    section: DraftSection


class ReviewResultEvent(BaseModel):
    kind: Literal["review_result"] = "review_result"
    passed: bool
    issues: list[ReviewIssue]


class EditingReadyEvent(BaseModel):
    kind: Literal["editing_ready"] = "editing_ready"


class SafetyTripEvent(BaseModel):
    kind: Literal["safety_trip"] = "safety_trip"
    safety: str
    message: str


class AgentFailedEvent(BaseModel):
    kind: Literal["agent_failed"] = "agent_failed"
    agent: str
    fallback_taken: str
    user_visible: bool = True


# --- discriminated union --------------------------------------------------


StreamEvent = Annotated[
    Union[
        SkeletonReadyEvent,
        FactsExtractedEvent,
        FillsAppliedEvent,
        AskUserEvent,
        EvidencesFoundEvent,
        DraftSectionEvent,
        ReviewResultEvent,
        EditingReadyEvent,
        SafetyTripEvent,
        AgentFailedEvent,
    ],
    Field(discriminator="kind"),
]
```

### 4.1 SSE 직렬화 규약

- `event` 필드: 항상 `"message"` (SSE 표준 이벤트 이름)
- `data` 필드: `StreamEvent.model_dump_json()` 결과 — 프론트가 `JSON.parse` → discriminator(`kind`)로 분기
- `id` 필드: 단조 증가하는 시퀀스 — 클라이언트 재연결 시 `Last-Event-ID`로 재전송 기준

---

## 5. 외부 API I/O (EXT 레이어)

`external/` 모듈은 외부 API 응답을 도메인 모델로 변환. 외부 응답 그대로 노출 금지.

```python
# external/law.py
from pydantic import BaseModel, Field
from datetime import datetime


class LawQuery(BaseModel):
    query: str
    article: str | None = None
    max_results: int = 5


class LawHit(BaseModel):
    citation: str       # "행정절차법 제22조 제3항"
    snippet: str
    source_url: str
    fetched_at: datetime


class LawResult(BaseModel):
    items: list[LawHit] = Field(default_factory=list)
    cache_hit: bool
    rate_limit_remaining: int | None = None
```

> stat.py, precedent.py도 동일 패턴.

---

## 6. 프론트엔드 타입 자동 동기화

### 6.1 절차

```
1. 백엔드 Pydantic 모델 변경
        ↓
2. FastAPI가 `/openapi.json` 자동 갱신 (런타임)
        ↓
3. 프론트 빌드 시 generate 단계:
   npx openapi-typescript http://127.0.0.1:8001/openapi.json -o src/api/generated.ts
        ↓
4. src/api/types.ts는 generated.ts 재export + 보조 별칭만
        ↓
5. tsc 컴파일 → 시그니처 mismatch 즉시 발견
```

### 6.2 자동화 스크립트

`src/frontend/package.json` 스크립트:

```json
{
  "scripts": {
    "gen:types": "openapi-typescript http://127.0.0.1:8001/openapi.json -o src/api/generated.ts",
    "predev": "npm run gen:types",
    "prebuild": "npm run gen:types"
  }
}
```

### 6.3 SSE 페이로드 타입

OpenAPI는 SSE 페이로드 스키마를 자동 노출하지 않음. 따라서:

- 백엔드가 `StreamEvent` discriminated union을 **별도 `GET /api/events/schema`** 엔드포인트로 노출 (JSON schema)
- 프론트는 이 엔드포인트에서도 타입 생성:
  `npx json-schema-to-typescript`로 `src/api/events.generated.ts`

또는 단순 접근: Pydantic 모델을 그대로 `model_json_schema()` 호출 → 정적 JSON 파일로 저장 → 빌드 시 변환.

### 6.4 CI 게이트

```yaml
# .github/workflows/interface-check.yml (개념)
- name: backend openapi diff
  run: |
    poetry run python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > new.json
    diff new.json baseline.json && echo "no change" || exit 1
- name: frontend types regen
  run: cd src/frontend && npm run gen:types && git diff --exit-code src/api/generated.ts
```

baseline은 ADR로 명시된 메이저 변경에서만 갱신.

---

## 7. 검증 패턴

### 7.1 모델 단위 검증

- `BaseModel.model_validate()` 호출 시 자동 검증
- `Field(ge=, le=, min_length=, ...)`로 제약 명시
- 도메인 검증(예: `Fact.value` 타입이 `FieldSpec.type`과 일치하는지)은 **도메인 함수**에 — 모델 자체에 두면 import 순환 발생

### 7.2 round-trip 테스트

모든 모델에 대해 M6가 자동:
```python
def test_serialization_roundtrip(sample):
    json_str = sample.model_dump_json()
    restored = type(sample).model_validate_json(json_str)
    assert restored == sample
```

fixture는 `fixtures/types/{module}.json` — 각 모델당 최소 1개의 정상 케이스 + 1개의 경계 케이스.

### 7.3 인터페이스 호환성

스키마가 추가만 되고 제거·rename 안 되는지 확인:
- `openapi-diff` 도구로 PR마다 비교
- breaking change면 ADR 동반 필수

---

## 8. Walking Skeleton과의 교체 절차

현재 `src/backend/app/shared/types.py` 단일 파일에 부분 직역이 있음. 교체 단계:

1. `src/backend/app/shared/types/` 디렉토리 생성, 본 명세대로 분할
2. 기존 `types.py`는 삭제, walking skeleton의 `sse.py`·`main.py`는 새 모듈 import로 갱신
3. 프론트 `src/frontend/src/api/types.ts`는 OpenAPI 생성 절차로 대체 — 기존 수기 정의는 제거
4. walking skeleton의 SSE 이벤트 4종(`skeleton_ready`, `draft_section`, `ask_user`, `editing_ready`)은 `events/stream.py`의 동일 이름 모델로 직접 호환됨 — 프론트 코드 변경 0

### 8.1 호환성 보존 사항

walking skeleton에서 사용한 이벤트 kind 이름과 페이로드 키는 본 명세와 일치 — 정식 부트스트랩이 들어와도 프론트가 다시 안 깨짐.

---

## 9. 결정 사항 요약

| 결정 | 내용 |
|---|---|
| 단일 진실 소스 | `src/backend/app/shared/types/` Pydantic 모델 |
| TS 타입 | OpenAPI → `openapi-typescript` 자동 생성, 수기 작성 금지 |
| 모듈 분할 | 도메인별 파일 + 에이전트별 I/O 별도 + 이벤트 별도 + 외부 API 별도 |
| Discriminated union | `Annotated[Union[...], Field(discriminator="kind")]` 표준 |
| 변경 게이트 | lead-architect 단독 권한, `references/interface-change-protocol.md` 적용 |
| 스트리밍 인터페이스 | `AsyncIterator[T]`는 모델 외부 함수 시그니처 (Pydantic 모델 안에 두지 않음) |
| 검증 자동화 | round-trip 테스트 + openapi-diff CI 게이트 |
| Walking skeleton 호환 | 이벤트 kind 이름·페이로드 키 유지 → 프론트 회귀 0 |

## 다음 단계 (B0-2·B0-3 unblock)

이 명세가 확정되면:

- **B0-2 (backend-engineer)** — `shared/types/` 디렉토리 본 구현, LLM 어댑터 + #1a·#1b·#2·#6 4개 에이전트 stub 작성. walking skeleton의 `sse.py`는 실제 오케스트레이터 호출로 교체.
- **B0-3 (frontend-engineer)** — `openapi-typescript`/`json-schema-to-typescript` 자동 생성 파이프라인 구성. shadcn/ui 통합 (디자인 토큰은 walking skeleton의 5색 status를 그대로).

walking skeleton에서 검증된 패턴(3패널 레이아웃, 5가지 status 색상, SSE 흐름)은 그대로 유지 — 본 명세는 그 위에 LLM·RAG·인증·라이브러리를 얹는 청사진.
