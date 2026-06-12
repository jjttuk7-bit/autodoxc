// 백엔드 베이스 URL — VITE_API_URL이 있으면 그것, 없으면 빈 문자열(상대 경로 → dev proxy).

const RAW = (import.meta.env.VITE_API_URL ?? "").trim();

/** trailing slash 제거. 빈 문자열이면 빈 문자열 반환(상대 경로 동작). */
export const API_BASE: string = RAW.replace(/\/+$/, "");

/** API 경로 prefix 헬퍼. path는 항상 `/`로 시작. */
export function apiUrl(path: string): string {
  if (!path.startsWith("/")) path = "/" + path;
  return `${API_BASE}${path}`;
}
