import type { StreamEvent } from "../api/types";

export async function connectStream(
  sessionId: string,
  onEvent: (e: StreamEvent) => void
): Promise<void> {
  const res = await fetch(`/api/sessions/${sessionId}/stream`);
  if (!res.ok || !res.body) {
    throw new Error(`stream failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE 파싱 — 이벤트는 빈 줄(\n\n)로 구분
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);

      // data: <json>\n 형태만 우선 처리 (event: ... 라인 무시)
      const dataLine = raw
        .split("\n")
        .find((l) => l.startsWith("data:"));
      if (!dataLine) continue;
      const json = dataLine.slice(5).trimStart();
      try {
        onEvent(JSON.parse(json) as StreamEvent);
      } catch (err) {
        console.error("SSE parse failed", err, json);
      }
    }
  }
}
