"""SkeletonNode + FieldSpec + SkeletonSource (discriminated union)."""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field


class FieldSpec(BaseModel):
    field_id: str
    label: str
    type: Literal["text", "number", "date", "money", "duration", "enum"]
    hint: str | None = None
    example: str | None = None
    fill_strategy: Literal["ask_user", "infer", "rag", "default"]


# --- SkeletonSource (discriminated union) ---------------------------------


class SourceOfficialForm(BaseModel):
    kind: Literal["official_form"] = "official_form"
    form_id: str
    agency: str


class SourceUserLibrary(BaseModel):
    kind: Literal["user_library"] = "user_library"
    entry_id: str
    usage_count: int = Field(ge=0)


class SourceRag(BaseModel):
    kind: Literal["rag"] = "rag"
    sample_ids: list[str] = Field(default_factory=list)


class SourceLlmInference(BaseModel):
    kind: Literal["llm_inference"] = "llm_inference"
    confidence: float = Field(ge=0.0, le=1.0)


class SourceUserAttached(BaseModel):
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


SkeletonNode.model_rebuild()
