# ADR 0005: 프론트엔드 — Vite + React SPA + shadcn/ui

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

3패널 워크벤치(채팅·캔버스·근거), Progressive form 시각화, SSE 스트리밍 클라이언트, 인라인 편집·키보드 단축키. UI 상태 머신 7개(`03-ui-model §6`)와 복잡한 클라이언트 상태. SaaS 워크벤치 성격이라 SSR/SSG 가치 낮음.

## 결정

**Vite + React 18 + TypeScript (SPA)** 채택.

**구체 스택**:
- 빌드: Vite (HMR 가장 빠름)
- 프레임워크: React 18 + TypeScript 5
- 라우팅: React Router v6
- 상태: Zustand (글로벌) + React Query (서버 상태) — Redux 보일러플레이트 회피
- 컴포넌트: shadcn/ui + Radix Primitives (접근성·키보드 표준)
- 스타일: Tailwind CSS + CSS Variables (디자인 토큰)
- 폼: React Hook Form (인라인 편집)
- 스트리밍: native `fetch` + `ReadableStream` (SSE)
- 테스트: Vitest + React Testing Library + Playwright (E2E)

## 대안

- **Next.js (App Router)**:
  - 장점: 풀스택 통합·SSR
  - 단점: 백엔드가 Python(D4)이라 풀스택 장점 안 쓰임. SSR 가치 낮음(워크벤치 앱). Turbopack/webpack 부담
- **SvelteKit**:
  - 장점: 코드 간결성·성능
  - 단점: 컴포넌트 라이브러리(특히 접근성 표준) React 대비 약함. 학습 곡선
- **SolidStart**:
  - 장점: signals 성능
  - 단점: 신생 — 생태계·도구 풍부도 떨어짐

## 결과

**영향 모듈**: 전체 `src/frontend/` 구조.

**프로젝트 구조 표준**:
```
src/frontend/
├── package.json
├── vite.config.ts
├── tailwind.config.ts
├── src/
│   ├── components/
│   │   ├── workbench/             # 3패널 컨테이너
│   │   ├── chat/
│   │   ├── canvas/                # Progressive form
│   │   ├── side-panel/
│   │   └── shared/
│   ├── state/
│   │   ├── session-store.ts       # Zustand
│   │   ├── ui-state-machine.ts    # 7개 상태
│   │   └── selectors.ts
│   ├── streaming/
│   │   ├── sse-client.ts
│   │   └── patch-applier.ts
│   ├── api/                       # openapi-typescript 생성 클라이언트
│   ├── tokens/                    # 디자인 토큰
│   └── main.tsx
└── tests/
```

**디자인 토큰 (5가지 status 색상)**:
```css
:root {
  --status-confirmed: var(--ink-base);
  --status-inferred-bg: oklch(0.94 0.05 95);   /* 옅은 노랑 */
  --status-defaulted: oklch(0.6 0 0);            /* 옅은 회색 */
  --status-evidence: oklch(0.6 0.15 230);        /* 파란 막대 */
  --status-empty: oklch(0.7 0 0);                /* 점선 박스 */
}
```

**SSE 클라이언트 패턴**:
```ts
async function connectStream(sessionId: string, onPatch: (patch: Patch) => void) {
  const res = await fetch(`/api/sessions/${sessionId}/stream`);
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE parse — 'data: ...\n\n'
    const events = parseSSEEvents(buffer);
    for (const e of events) onPatch(JSON.parse(e.data));
    buffer = leftover(buffer);
  }
}
```

**백엔드 인터페이스 공유**: D4의 OpenAPI에서 `openapi-typescript`로 클라이언트 타입 생성 — 경계면 mismatch 자동 검출.

**접근성**:
- Radix Primitives의 `aria-*` 표준 활용
- 5가지 status 색상은 색약 대비 + 항상 아이콘/라벨 보조
- `aria-live` 영역으로 상태 변화 음성 알림

**모바일 반응형**:
- 1280px 이상: 3패널
- 1024~1279px: 우 패널 모달
- 1024px 미만: 캔버스 전체화면 + 하단 시트 탭

**회귀 검증**: M6가 Playwright로 시나리오 S1~S5 자동화.
