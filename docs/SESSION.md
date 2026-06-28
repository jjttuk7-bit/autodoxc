# autodoxc — Session Status

> **목적**: 다음 세션 진행 시 이 파일을 먼저 확인. 어디까지 됐고 어디로 갈지 한눈에.
> **마지막 갱신**: 2026-06-28
> **메인 브랜치 HEAD**: `f90c4b7`+ — 시드 13종(행정 구제·신청 6 + 계약·소송 4 + 레거시 3) (prod 0.0.14)
> **출력 원칙**: 완성된 실제 문서를 만드는 게 목적(메타 설명 금지). 주요 문서는 시드(Track A), 롱테일은 LLM 폴백.
> **🔴 미해결 보안**: 진단 중 OpenAI 키가 스트림/로그에 노출됨 → **키 재발급(rotate) 필요**. 또 `OPEN_LAW_OC`가 프로덕션에 미설정(`not configured`)으로 확인됨 → 법령 근거 prod 미작동.

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
10. **법령 근거 자동 검증 (#5 EvidenceRetriever 1단계)** — 시드 doc_type 본문이 인용한 법령(외국인근로자고용법·행정절차법·민법)을 국가법령정보센터 API로 실시간 조회 → `evidences_found` SSE 이벤트 + `/state.evidences`로 노출. 생성 Evidence.id가 시드 evidence_refs와 일치해 문단↔근거 연결 가능. (프론트 근거 패널 렌더링은 미연결 — 다음 단계)
11. **첨부 양식 → 골격 추출** — 시작 화면 「양식 첨부」로 `.docx/.pdf/.txt` 업로드 → DA4 파서로 파싱 → heading 구조를 골격(`att_sec_N`, source=`user_attached`)으로 추출 → stream 시 SkeletonComposer 대신 채택(소스 우선순위 최상위). 텍스트 없이 첨부만으로도 시작 가능. 제목 없는 문서는 폴백(일반 구성).
12. **모든 문서 종류 작성 (doc_type LLM 분류)** — 시드 3종 외 입력도 LLM 구조화 분류(`DOC_TYPE_SYSTEM`)로 canonical id·ko_name·domain 도출 → SkeletonComposer가 종류별 골격 생성. 예: 사업자등록증→business-registration(permit)→신청인/요건/첨부 골격. (이전엔 전부 "행정문서 일반"+목적/배경/분석 generic이었음). prod 0.0.8 검증 완료.

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
| **#22 B1-5** | 시드 코퍼스 RAG 인덱싱 (관련 법령·재결례 50~100건) | 법령 인용·근거 자동 보강 | **Postgres + pgvector** 필요 — 단, 법령 단건 검증은 #5 EvidenceRetriever 1단계로 **선반영** (API 직접 조회, RAG 무관) |
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

## 5.5 "완성됐는데 본선 미연결" 인벤토리 (2026-06-28 전수 점검)

> 부품은 만들어졌으나 오케스트레이터(`main_sequence.py`)·API에 안 물린 것. 새로 만들 게 아니라 **배선**이 남은 것들.

| 부품 | 완성도 | 막힌 지점 | 연결에 필요한 것 |
|---|---|---|---|
| **법령 API (`LawClient`)** | ✅ 완성·테스트, OC 키 Railway 라이브 | ~~호출 코드 0~~ → **#5에서 연결됨** | (1단계 완료) |
| **#5 EvidenceRetriever** | ✅ **1단계 구현·본선 연결** (`app/agents/evidence_retriever.py`) | statute만 / 시드 doc_type만 | 2단계: 판례·통계·RAG 소스 + LLM 본문 evidence_needs |
| **DA4 파서 파이프라인** | ✅ docx/pdf/txt (`app/parsers/`) | ~~업로드 엔드포인트 없음~~ → **연결됨** (`POST /attachment` → `skeleton_extract` → 골격) | (1단계 완료) PDF OCR·hwp·이미지는 B2 |
| **RAG 레이어** | ✅ 하이브리드 검색 (`app/data/rag/`) | DATABASE_URL 비어 `get_pool()` None → `[]`; 호출 0; 코퍼스 미인덱싱 | DB 연결 + 코퍼스 인덱싱 + 검색 호출처 |
| **#3 GapAnalyzer** | 🟡 모킹 (doc_type별 고정 질문 1개) | 시스템적 갭 진단 없음 | 본구현 |
| **#4 LogicArchitect** | ❌ 미구현 | — | 신규 (evidence_needs 생성 → #5 공급) |
| **#7 SelfReviewer** | ❌ 미구현 (모킹 생략) | — | 신규 |

가성비 순: ① ~~법령 연결(완료)~~ → ② ~~첨부 업로드→DA4→골격(완료)~~ → ③ DB(Supabase)→RAG 가동 → ④ #4 LogicArchitect → #5 2단계(판례·통계).

---

## 6. 명세 외 UX·기능 갭 (작업하며 발견)

| 항목 | 현재 상태 | 효과 |
|---|---|---|
| **첨부 파일 업로드** | ✅ **연결됨** — `.docx/.pdf/.txt`. heading 있으면 user_attached 골격, 없으면(PDF 양식 등) **파일명+원문으로 doc_type 분류 + 내용 기반 LLM 골격**(0.0.9). 남은 것: 스캔본(텍스트 레이어 없음)은 파일명만 의존(OCR은 B2); 양식을 본문 *시드*로 쓰는 건 미구현 | 사용자 양식을 골격으로 즉시 채택 |
| **사이드 패널 — 근거 탭** | 백엔드는 `evidences_found`·`/state.evidences`로 법령 근거 제공하나 프론트 렌더링 X (`session-store` switch에 `evidences_found` 케이스 없음) | 검증된 법령을 클릭형 근거로 표시 |
| **사이드 패널 — 라이브러리 탭** | 비활성 | 보조 정보 한눈에 |
| **인라인 질문 1턴 1개 → 다중** | 단일 질문만 모킹 | 더 풍부한 갭 분석 |
| **DB 영속화** | 메모리만. Railway 재시작 시 사라짐 | Supabase Postgres 연결로 영구 |
| **추정값 팝오버** | 노란 배경만, 근거 표시 X | 신뢰 확보 |
| **저장 버튼 활성화** | 헤더에 [저장] 버튼 비활성 (placeholder) | 명시적 마일스톤 |
| **.pdf / .hwp 내보내기** | .docx만 | 형식 다양화 |
| **시드 doc_type** | 13종 — 레거시 3종(외국인 고용·내용증명·행정심판 청구서) + 데이터 10종: 행정 구제·신청 6(정보공개·사업자등록·이의신청·행정심판답변·영업신고·의견제출) + 계약 2(주택임대차·근로) + 소송 2(대여금소장·준비서면). `app/agents/seed_docs.py` 데이터로 선언. 키워드: 데이터 시드 우선 | 50선 계속 확충 |

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
- **법령 근거 — 프론트 미렌더링** — 백엔드 #5는 `evidences_found` 이벤트·`/state.evidences`를 내보내나 `session-store.ts` switch에 케이스가 없어 화면에 안 보임(무해하게 무시됨). 근거 패널 연결이 다음 프론트 작업.
- **법령 근거 — 시드 doc_type만** — `_SEED_STATUTE_NEEDS`에 등록된 3종(외국인고용·행정심판·내용증명)만 검증. LLM 생성 본문은 evidence_refs가 없어 #5가 동작 안 함. doc_type 추가 시 시드 매핑 동반 필요.
- **법령 인용 표시값은 시드 고정** — Evidence.citation의 정밀 조문(「민법」제390조)은 `_SEED_STATUTE_NEEDS`의 표시 문자열. API는 법령 존재·source_url 검증만 (조문 단위 조회 아님). 조문 단위 정밀 조회는 2단계.
- **첨부 골격 본문은 stub/LLM** — 첨부 양식의 `att_sec_N`은 시드 본문 매핑이 없어 DraftWriter가 generic stub(시드 doc_type일 때) 또는 LLM(비시드 doc_type)으로 채움. 첨부 양식 자체의 문구를 본문 시드로 쓰는 건 미구현.
- **첨부 양식 비영속** — 파싱 후 임시파일 즉시 삭제, 추출 골격만 메모리 세션에 보관(`ctx.attached_skeleton`). Railway 재시작 시 사라짐. storage_uri 영구 저장은 DB·오브젝트 스토리지 도입 후.
- **`python-multipart` 의존 추가** — 업로드용. `pyproject.toml`에 반영했으나 배포(Railway) 재빌드 시 설치 확인 필요.
- **[해결됨] 비시드 문서 빈 스텁 — 키 공백 버그** — 2026-06-28 진단. 프로덕션 `OPENAI_API_KEY`에 trailing `\n` + leading space가 섞여 `Authorization` 헤더가 깨짐(`LocalProtocolError: Illegal header value`) → 모든 LLM 호출이 `APIConnectionError`로 실패 → 시드 외 문서가 빈 스텁. **코드/키/billing 문제 아니었음.** `config.py`에서 키를 `.strip()`으로 정규화해 수정(`f5949be`). 교훈: 환경변수 비밀값은 항상 strip. 단, **Railway 환경변수 자체도 깨끗이 재입력 권장**(개행 제거).
- **[보안] 진단 중 키 노출** — `AgentFailedEvent`가 에러 메시지에 키 전문을 스트림으로 노출했음. 지금은 `redact_secrets`로 마스킹(`sk-*`/`Bearer`). 그러나 노출된 키는 **반드시 폐기·재발급**. (이 세션 로그·커밋 이전 시점 스트림에 평문 존재)
- **[미설정] `OPEN_LAW_OC` 프로덕션 부재** — prod 스트림 진단에서 `evidence_retriever: 법령 조회 실패: OPEN_LAW_OC not configured` 확인. Railway에 OC 변수가 비어있거나 미설정 → #5 법령 근거가 prod에서 동작 안 함. Railway 환경변수 점검 필요.

---

## 11. 핵심 파일 위치 (빠른 참조)

| 영역 | 파일 |
|---|---|
| 백엔드 진입 | `src/backend/app/main.py` |
| 세션 endpoint | `src/backend/app/api/sessions.py` |
| 오케스트레이터 | `src/backend/app/orchestrator/main_sequence.py` |
| 에이전트 5개 | `src/backend/app/agents/{doc_type_identifier,skeleton_composer,facts_extractor,draft_writer,evidence_retriever}.py` |
| 법령 근거 시드 매핑 | `src/backend/app/agents/evidence_retriever.py:_SEED_STATUTE_NEEDS` (evidence_id ↔ 검색어 ↔ 표시 인용) |
| 법령 API 클라이언트 | `src/backend/app/data/external/law_api.py:LawClient` |
| 첨부 골격 추출 | `src/backend/app/parsers/skeleton_extract.py:skeleton_from_parse` (heading → att_sec_N) |
| 첨부 업로드 endpoint | `src/backend/app/api/sessions.py:upload_attachment` (`POST /api/sessions/{id}/attachment`) |
| 프론트 업로드 UI | `src/frontend/src/components/start/StartScreen.tsx` (양식 첨부) + `client.ts:uploadAttachment` |
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
