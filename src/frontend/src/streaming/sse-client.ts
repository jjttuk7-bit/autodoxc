import { apiUrl } from "../api/base";
import type { StreamEvent } from "../api/types";

/**
 * SSE 연결 — 표준 EventSource API 사용.
 * 백엔드는 sse-starlette로 `event: message\ndata: {...}\n\n` 형식 전송 →
 * 브라우저의 EventSource가 onmessage로 처리.
 *
 * editing_ready 이벤트 도착 시 자동 종료(resolve). 네트워크 오류 시 reject.
 */
export function connectStream(
  sessionId: string,
  onEvent: (e: StreamEvent) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const url = apiUrl(`/api/sessions/${sessionId}/stream`);
    const es = new EventSource(url);

    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as StreamEvent;
        onEvent(data);
        if (data.kind === "editing_ready") {
          es.close();
          resolve();
        }
      } catch (err) {
        console.error("SSE parse failed", err, ev.data);
      }
    };

    es.onerror = (ev) => {
      // editing_ready로 정상 종료된 경우 readyState=CLOSED — 이미 resolve됨
      if (es.readyState === EventSource.CLOSED) {
        return;
      }
      console.error("SSE connection error", ev, "readyState=", es.readyState);
      es.close();
      reject(new Error("SSE connection error"));
    };
  });
}
