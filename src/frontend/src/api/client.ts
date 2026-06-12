// 세션 생성 + SSE 연결 묶음 — B1-1 endpoint 활용

import type { components } from "./generated";
import { apiUrl } from "./base";
import { connectStream } from "../streaming/sse-client";
import type { StreamEvent } from "./types";

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
