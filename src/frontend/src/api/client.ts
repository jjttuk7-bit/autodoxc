// 세션 생성·스트리밍·편집 API 묶음

import type { components } from "./generated";
import { apiUrl } from "./base";
import { connectStream } from "../streaming/sse-client";
import type { DraftSection, StreamEvent } from "./types";

type CreateSessionRequest =
  components["schemas"]["CreateSessionRequest"];
type CreateSessionResponse =
  components["schemas"]["CreateSessionResponse"];

export async function createSession(
  userInput: string
): Promise<CreateSessionResponse> {
  const body: CreateSessionRequest = { user_input: userInput };
  const res = await fetch(apiUrl("/api/sessions"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`createSession failed: ${res.status}`);
  }
  return (await res.json()) as CreateSessionResponse;
}

export async function startSessionStream(
  sessionId: string,
  onEvent: (e: StreamEvent) => void
): Promise<void> {
  await connectStream(sessionId, onEvent);
}

// --- B1-4: 인라인 편집·답변 ----------------------------------------------

interface FillResponse {
  section: DraftSection;
}

interface AnswerResponse {
  acknowledged: boolean;
  facts_added: number;
  skipped: boolean;
}

/** 빈/추정 문단을 사용자 입력으로 채움. 백엔드가 confirmed로 승격된 섹션 반환. */
export async function fillSlot(
  sessionId: string,
  sectionId: string,
  paragraphIdx: number,
  text: string
): Promise<DraftSection> {
  const res = await fetch(apiUrl(`/api/sessions/${sessionId}/fill`), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      section_id: sectionId,
      paragraph_idx: paragraphIdx,
      text,
    }),
  });
  if (!res.ok) {
    throw new Error(`fillSlot failed: ${res.status}`);
  }
  const data = (await res.json()) as FillResponse;
  return data.section;
}

/** 인라인 질문 답변. 백엔드 facts에 추가. skip=true면 건너뜀 기록만. */
export async function answerQuestion(
  sessionId: string,
  fieldIds: string[],
  value: string,
  skip: boolean = false
): Promise<AnswerResponse> {
  const res = await fetch(apiUrl(`/api/sessions/${sessionId}/answer`), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      field_ids: fieldIds,
      value,
      skip,
    }),
  });
  if (!res.ok) {
    throw new Error(`answerQuestion failed: ${res.status}`);
  }
  return (await res.json()) as AnswerResponse;
}
