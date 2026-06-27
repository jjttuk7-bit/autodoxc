// 세션 생성·스트리밍·편집·복구·내보내기 API 묶음

import type { components } from "./generated";
import { apiUrl, API_BASE } from "./base";
import { connectStream } from "../streaming/sse-client";
import type {
  DocType,
  DraftSection,
  Evidence,
  Fact,
  SkeletonNode,
  StreamEvent,
} from "./types";

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

export interface AttachmentUploadResponse {
  attachment_id: string;
  file_name: string;
  format: string;
  extracted: boolean;
  section_titles: string[];
  warnings: string[];
}

/** 첨부 양식 업로드 → 백엔드가 DA4로 파싱·골격 추출. stream 시작 전에 호출. */
export async function uploadAttachment(
  sessionId: string,
  file: File
): Promise<AttachmentUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(apiUrl(`/api/sessions/${sessionId}/attachment`), {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return (await res.json()) as AttachmentUploadResponse;
}

// --- B1-4: 인라인 편집·답변 ----------------------------------------------

interface FillResponse {
  section: DraftSection;
}

interface AnswerResponse {
  acknowledged: boolean;
  facts_added: number;
  skipped: boolean;
  updated_sections: DraftSection[];
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

// --- 복구 + 내보내기 -----------------------------------------------------

export interface SessionStateResponse {
  session_id: string;
  user_input: string;
  doc_type: DocType | null;
  skeleton: SkeletonNode[];
  facts: Fact[];
  sections: DraftSection[];
  evidences?: Evidence[];
  is_complete: boolean;
  updated_at: string;
}

/** 세션 복구 — URL ?s=xxx 등으로 sessionId가 알려진 상황에서 호출. */
export async function getSessionState(
  sessionId: string
): Promise<SessionStateResponse> {
  const res = await fetch(apiUrl(`/api/sessions/${sessionId}/state`));
  if (res.status === 404) {
    throw new Error("session not found");
  }
  if (!res.ok) {
    throw new Error(`getSessionState failed: ${res.status}`);
  }
  return (await res.json()) as SessionStateResponse;
}

/** 완성된 문서를 .docx로 다운로드. 새 탭에서 직접 호출. */
export function exportDocxUrl(sessionId: string): string {
  return `${API_BASE}/api/sessions/${sessionId}/export?format=docx`;
}
