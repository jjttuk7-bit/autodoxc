// 백엔드 타입 — `src/backend/app/shared/types/`가 단일 진실 소스.
// generated.ts는 npm run gen:types로 자동 생성 (predev/prebuild 훅).
// 이 파일은 generated.ts의 컴포넌트 스키마에 편한 별칭을 제공한다.

import type { components } from "./generated";

type S = components["schemas"];

// --- 도메인 ---
export type Domain = S["DocType"]["domain"];
export type DocType = S["DocType"];
export type SkeletonNode = S["SkeletonNode"];
export type FieldSpec = S["FieldSpec"];
export type SkeletonSource = S["SkeletonNode"]["source"];

// --- 사실·근거·논리 ---
export type Fact = S["Fact"];
export type Evidence = S["Evidence"];
export type EvidenceNeed = S["EvidenceNeed"];
export type LogicNode = S["LogicNode"];

// --- 초안 ---
export type Draft = S["Draft"];
export type DraftSection = S["DraftSection"];
export type DraftParagraph = S["DraftParagraph"];
export type ParagraphAnnotation = S["ParagraphAnnotation"];
export type ParagraphStatus = ParagraphAnnotation["status"];
export type EmptySlot = S["EmptySlot"];

// --- 인터랙션 ---
export type Question = S["Question"];
export type Assumption = S["Assumption"];

// --- 세션 ---
export type SessionState = S["SessionState"];
export type Attachment = S["Attachment"];
export type Message = S["Message"];

// --- SSE 이벤트 ---
export type SkeletonReadyEvent = S["SkeletonReadyEvent"];
export type FactsExtractedEvent = S["FactsExtractedEvent"];
export type FillsAppliedEvent = S["FillsAppliedEvent"];
export type AskUserEvent = S["AskUserEvent"];
export type EvidencesFoundEvent = S["EvidencesFoundEvent"];
export type DraftSectionEvent = S["DraftSectionEvent"];
export type ReviewResultEvent = S["ReviewResultEvent"];
export type EditingReadyEvent = S["EditingReadyEvent"];
export type SafetyTripEvent = S["SafetyTripEvent"];
export type AgentFailedEvent = S["AgentFailedEvent"];

// SchemaBundle.stream_event는 백엔드에서 union으로 정의됨 — 그대로 차용
export type StreamEvent = S["SchemaBundle"]["stream_event"];
