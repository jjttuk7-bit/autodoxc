# autodoxc — Session Status

> **목적**: 다음 세션 진행 시 이 파일을 먼저 확인. 어디까지 됐고 어디로 갈지 한눈에.
> **마지막 갱신**: 2026-06-13
> **메인 브랜치 HEAD**: `f7de4c8` — 자리표시자 부분만 인라인 input

---

## 1. 현재 배포 상태

| 영역 | 위치 |
|---|---|
| 프론트엔드 | https://autodoxc.vercel.app (Vite + React 18 + shadcn/ui + Tailwind v4 + Zustand) |
| 백엔드 | https://autodoxc-production.up.railway.app (FastAPI + Pydantic v2 + sse-starlette) |
| 깃허브 | https://github.com/jjttuk7-bit/autodoxc |
| LLM | OpenAI **gpt-4o** + **gpt-4o-mini** (티어 분리, ADR 0010) |
| 외부 API | 국가법령정보센터 OpenAPI (OPEN_LAW_OC 등록됨) |
| **DB** | **미연결** (DATABASE_URL 비어있음 → RAG·라이브러리 noop) |

**환경변수**:
- Railway: `OPENAI_API_KEY`, `OPEN_LAW_OC`, `LLM_PROVIDER=openai`
- Vercel: `VITE_API_URL=https://autodoxc-production.up.railway.app`

---

## 2. 완료된 가치 흐름 (Phase B1 핵심)

사용자가 `autodoxc.vercel.app` 진입 후 가능한 모든 동작:

1. **자유 입력** → 한 줄 텍스트
2. **세션 생성** → URL에 `?s=세션ID` 자동 기록
3. **SSE 스트리밍** — 5섹션 점진 등장 (0.4초 간격)
   - 시드 doc_type (외국인 고용·내용증명·행정심판) → 시드 본문
   - 시드 없는 doc_type → **GPT-4o가 골격·본문 생성**
4. **5가지 status 색상** — confirmed / inferred / defaulted / evidence_backed / empty
5. **자리표시자 부분 채움** — `[[필드명]]` 배지 클릭 → 인라인 input → 그 부분만 치환
6. **인라인 질문 답변** → 영향 섹션 자동 재작성 (시드 doc_type은 자리표시자 치환, 그 외는 LLM 호출)
7. **세션 영속** — Railway 메모리 + URL 복구 → 새로고침 후에도 작업 유지
8. **`.docx` 다운로드** — `[[..]]`는 `(  필드명          )`로 변환, 행정문서 표준 빈 칸
9. **새 세션** 버튼 → URL 정리 + 처음으로

---

## 3. 명세·자산 인덱스 (참조)

| 영역 | 위치 |
|---|---|
| 명세 5편 + 인터페이스 직역 | `docs/architecture/01~06.md` |
| ADR 10건 | `docs/adr/0001~0010.md` (0001은 0010로 supersede) |
| 도메인 자산 | `docs/domain/seed-forms/list.md` 등 7편 (행정사 검토 대기) |
| 외부 의존성 결정 요약 | `docs/architecture/decisions/external-dependencies.md` |
| 하네스 (에이전트 6명 + 스킬) | `.claude/agents/`, `.claude/skills/autodoxc-build/` |
| 트리거 검증 | `.claude/skills/autodoxc-build/references/trigger-tests.md` |

---

## 4. Phase B1 남은 Task

| Task | 내용 | 가치 | 외부 의존 |
|---|---|---|---|
| **#22 B1-5** | 시드 코퍼스 RAG 인덱싱 (관련 법령·재결례 50~100건) | 법령 인용·근거 자동 보강 | **Postgres + pgvector** 필요 |
| **#23 B1-6** | 도메인 검증 — LLM-as-judge 활성화 + 톤·법령 인용 회귀 fixture | 품질 보증 | 없음 |
| **#24 B1-7** | E2E S1 시나리오 자동화 (Playwright) | 회귀 인프라 | 없음 |

---

## 5. Phase B2~B4 (명세상 — `docs/architecture/05-dev-team.md §5`)

### **Phase B2 — 인터랙션 강화** (3~4주 명세)
- **`#3` GapAnalyzer 본구현** — 모든 답변에 대한 시스템적 갭 진단
- **DA4 파서 정식 확장** — `.hwp` / `.hwpx` / `.pdf(스캔)` / 이미지(OCR)
- **첨부 양식 업로드 UX** — 캔버스에 파일 드롭 → DA4가 골격 추출 → 새 시드 1순위 소스
- **인라인 편집 UX 추가** — Undo/Redo, 다중 선택
- **추정값(InferredSpan) 팝오버** — 추정 근거 + [그대로 사용] / [수정] / [질문 받기]

### **Phase B3 — 다중 문서 + 라이브러리** (3~4주)
- **`#4 LogicArchitect`** — IRAC 등 도메인별 논리 구조
- **`#5 EvidenceRetriever`** — 법령·판례·통계 자동 retrieval
- **`#7 SelfReviewer`** — 톤·논리 자체 검토
- **`#8 SkeletonLearner`** — 사용자 작성 골격을 라이브러리에 누적
- **DA2 personal / shared 2계층 라이브러리**
- **인증 (Clerk)** + 사무소 단위 권한
- **PII 게이트** (정규식 + NER + LLM 3중)

### **Phase B4 — 운영화** (2~3주)
- 텔레메트리·관측성 (이벤트 8종, 메트릭 5개)
- 모바일 반응형 + 접근성
- 공용 라이브러리 승격 파이프라인
- 운영 매뉴얼·런북
- 한국 클라우드 마이그레이션 평가 (ADR 0009)

---

## 6. 명세 외 UX·기능 갭 (작업하며 발견)

| 항목 | 현재 상태 | 효과 |
|---|---|---|
| **첨부 파일 업로드** | UI 시안 있고 백엔드 파서(DA4) 있음, 연결 X | 사용자 양식을 골격으로 즉시 채택 |
| **사이드 패널** | 골격 탭만 부분 작동, 근거/라이브러리 비활성 | 보조 정보 한눈에 |
| **인라인 질문 1턴 1개 → 다중** | 단일 질문만 모킹 | 더 풍부한 갭 분석 |
| **DB 영속화** | 메모리만. Railway 재시작 시 사라짐 | Supabase Postgres 연결로 영구 |
| **추정값 팝오버** | 노란 배경만, 근거 표시 X | 신뢰 확보 |
| **저장 버튼 활성화** | 헤더에 [저장] 버튼 비활성 (placeholder) | 명시적 마일스톤 |
| **.pdf / .hwp 내보내기** | .docx만 | 형식 다양화 |
| **시드 doc_type 추가** | 3종만 (외국인 고용·내용증명·행정심판) | 도메인 시드 list.md의 50선 중 7~10개 P0 추가 |

---

## 7. 우선순위 추천

### A 그룹 — 즉시 가치, 낮은 비용 (외부 의존 0)
| 순위 | 항목 | 시간 | 비용 |
|---|---|---|---|
| 1 | **첨부 파일 업로드 → 골격 추출** | 1~2시간 | 0 |
| 2 | **시드 doc_type 추가** (P0 7~10개) | 2~3시간 | 0 |
| 3 | **추정값 팝오버** | 1시간 | 0 |
| 4 | **인라인 질문 다중화** (GapAnalyzer 단순) | 2~3시간 | LLM 호출 ↑ |

### B 그룹 — 인프라, 외부 의존 필요
| 순위 | 항목 | 외부 의존 |
|---|---|---|
| 5 | **Supabase 연결 + 영구 영속화** | Supabase 가입 |
| 6 | **B1-5 RAG 코퍼스 인덱싱** | 위 + 코퍼스 큐레이션 |

### C 그룹 — 품질·운영
| 순위 | 항목 |
|---|---|
| 7 | **B1-6 도메인 검증** (LLM-as-judge 활성화) |
| 8 | **B1-7 Playwright E2E** |
| 9 | **B4 텔레메트리·모바일·접근성** |

---

## 8. 다음 세션 1수 후보

가장 추천 — **A 그룹 1번 첨부 파일 업로드 → 골격 추출**
- DA4 파서·SkeletonComposer 이미 작성됨, UI 연결만
- 사용자 양식이 즉시 골격이 되는 강력한 시연 가치
- 외부 의존 0

---

## 9. 다음 세션 시작 가이드

새 Claude Code 세션 열면:

1. `D:\autodoxc` 디렉토리 작업
2. `CLAUDE.md` 자동 로딩 → `autodoxc-build` 스킬 트리거 대기
3. 사용자가 첫 메시지에 **"`docs/SESSION.md` 먼저 확인해줘"** 또는 그냥 작업 요청
4. 작업 시작 전 이 파일 갱신 (마지막 commit, 새 상태)

### 권장 첫 입력 패턴
- `"docs/SESSION.md 보고 다음 1수 — 첨부 파일 업로드 부분 진행해줘"`
- `"docs/SESSION.md 확인하고 B1-6부터 가자"`
- `"docs/SESSION.md 갱신해줘"`

---

## 10. 알려진 한계 (참조용)

- **메모리 세션** — Railway 재시작 시 모든 세션 사라짐. 동작은 OK, 영속성은 다음 단계.
- **GitHub commit 작성자** — `GitHub User <user@example.com>` (기본값). 본인 정보로 amend 가능 (`git config user.* + git commit --amend --reset-author`).
- **자리표시자 매핑 일부 누락** — 외국인 고용 sec_3/sec_4의 `[[교육 대상 인원]]`, `[[연간 매출 목표]]` 같은 자리표시자에 대한 field_id 매핑이 없음 — 답변 받아도 부분 재작성 X. `app/agents/draft_writer.py:_FIELD_PLACEHOLDERS`에 추가 필요.
- **시드 본문에 facts 인터폴레이션 불완전** — `industry`/`core_skill` 같은 일부만. 새 자리표시자 추가 시 매핑 동반 필요.
- **자동 npm run gen:types 안 됨 (배포 환경)** — 백엔드 OpenAPI 변경 시 로컬에서 한 번 실행 후 푸시 필요.
- **편집 작성자 정보** — 한 IP에서 여러 세션 가능 (인증 X). Phase B3 인증 도입 전까지 공유 X.

---

## 11. 핵심 파일 위치 (빠른 참조)

| 영역 | 파일 |
|---|---|
| 백엔드 진입 | `src/backend/app/main.py` |
| 세션 endpoint | `src/backend/app/api/sessions.py` |
| 오케스트레이터 | `src/backend/app/orchestrator/main_sequence.py` |
| 에이전트 4개 | `src/backend/app/agents/{doc_type_identifier,skeleton_composer,facts_extractor,draft_writer}.py` |
| LLM 어댑터 | `src/backend/app/llm/adapter.py` |
| 시드 본문 | `src/backend/app/agents/draft_writer.py:_foreign_worker_section` 등 |
| 자리표시자 매핑 | `src/backend/app/agents/draft_writer.py:_FIELD_PLACEHOLDERS` |
| 영향 섹션 매핑 | `src/backend/app/api/sessions.py:_FIELD_TO_SECTION` |
| 프론트 진입 | `src/frontend/src/App.tsx` |
| Zustand 스토어 | `src/frontend/src/state/session-store.ts` |
| 캔버스 | `src/frontend/src/components/canvas/{Canvas,EditableParagraph}.tsx` |
| API 클라이언트 | `src/frontend/src/api/client.ts` |
| SSE 클라이언트 | `src/frontend/src/streaming/sse-client.ts` |
| 자동 생성 타입 | `src/frontend/src/api/generated.ts` (백엔드 OpenAPI) |

---

## 12. 갱신 체크리스트

다음 세션 종료 시 이 파일에서 갱신할 것:
- [ ] §1 마지막 commit (`git log -1 --oneline`)
- [ ] §2 새 가치 흐름 추가
- [ ] §4 Phase B1 task 상태
- [ ] §6 새 UX 갭 발견 시 추가
- [ ] §7 우선순위 재조정
- [ ] §10 새로운 한계 발견 시 추가
- [ ] §11 새 핵심 파일 추가 시
