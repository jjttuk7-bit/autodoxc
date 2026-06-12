# 외부 의존성 결정 요청서 (Phase B0 진입 전)

> **작성**: lead-architect 역할
> **상태**: All Accepted (2026-06-12) — ADR 0001~0009로 분리 완료
> **원칙**: 각 항목 최소 2개 후보 비교, 추천안 1순위 명시. 단일 후보 옹호 금지.
> **공통 제약**:
> - 한국어 행정문서 도메인 (톤·법령 인용 정확성)
> - 멀티유저 + 사무소 단위 권한 (DA2 personal/shared 2계층)
> - 개인정보보호법·전자정부 보안 가이드 준수 필요
> - 소규모 시작 → 사용량 따라 확장 (콜드스타트 비용 < 운영 비용 가중치)

---

## D1. LLM 공급자

### 컨텍스트
런타임 에이전트 8개 + 사이드라인 #8이 LLM 호출. 에이전트별 난이도 차등(분류/추출 < 추론/검토)이므로 단일 모델보다 **티어 분리**가 비용 효율적.

### 후보 비교

| 항목 | Anthropic Claude (1순위 추천) | OpenAI GPT | 국내 (HyperCLOVA X·Solar) |
|---|---|---|---|
| 한국어 톤·문서 작성 | 매우 우수 (행정 톤 일관) | 우수 | 우수 (국내 도메인 강점) |
| 법령 인용 정확성 | 우수 (할루시네이션 적음) | 중상 | 우수 (국내 법령 학습) |
| 도구·구조화 출력 | tool_use·extended thinking·JSON 우수 | function calling·structured output 우수 | 도구 통합 미흡 (개선 중) |
| 컨텍스트 윈도우 | 200K (Opus/Sonnet) | 128K~1M | 32K~128K (모델별) |
| 비용 (입력 1M 토큰) | Opus $15·Sonnet $3·Haiku $0.80 | $5~$10 / $0.40~$0.60 | $1~$3 (모델별) |
| Prompt caching | 5분 TTL, 90% 할인 | 1시간 TTL, 50% 할인 | 미지원 또는 제한 |
| 한국 데이터 처리 | 미국 호스팅 (개인정보 검토 필요) | 미국 호스팅 (동일) | 국내 호스팅 (개인정보 유리) |
| 운영 리스크 | API 의존 | API 의존 | 모델 안정성·기능 격차 |

### 추천: **Anthropic Claude 티어 분리**

| 에이전트 | 모델 | 이유 |
|---|---|---|
| #1a DocTypeIdentifier | Haiku 4.5 | 분류, 짧은 입력, 빠른 응답 |
| #1b SkeletonComposer | Sonnet 4.6 | 구조 합성, 우선순위 처리 |
| #2 FactsExtractor | Sonnet 4.6 | 추출, 정규화 |
| #3 GapAnalyzer | Sonnet 4.6 → Opus 4.7 (추론 무거울 시) | 갭 진단, 질문 생성 |
| #4 LogicArchitect | Opus 4.7 | 추론 핵심 — 논리 구조 |
| #5 EvidenceRetriever | Haiku 4.5 (검색 쿼리 생성만) | LLM 호출 가벼움, 외부 API 위주 |
| #6 DraftWriter | Sonnet 4.6 | 본문 작성, 톤 일관 |
| #7 SelfReviewer | Opus 4.7 | 정확성 검토 |
| #8 SkeletonLearner | Sonnet 4.6 | 비동기, diff·merge |

**근거**:
- 행정문서 톤 + 법령 인용 정확성에서 Claude의 강점이 가장 가치 있는 영역
- Prompt caching 90% 할인이 골격·시드·도메인 가이드 같은 정적 컨텍스트에 직접 적용 가능
- tool_use·구조화 출력이 안정적 — `01-agents.md`의 모든 출력이 JSON 직렬화 필요

### 보충 의견
- 한국 데이터 컴플라이언스가 엄격해지면 국내 모델 fallback 트랙 검토. M2 LLM 어댑터를 공급자 추상화로 두면 교체 비용 낮음.
- 비용 모니터링 임계치를 두고, 운영 단계에서 트래픽 패턴 따라 일부를 국내 모델로 분기 가능.

### 결정 필요
- [ ] Anthropic Claude 티어 분리 채택?
- [ ] 비용 상한 (월·세션) 임계치 — `04-orchestration §8` token budget의 구체 값

---

## D2. 임베딩 모델

### 컨텍스트
DA3 RAG 인덱스 + 사용자 골격 라이브러리 검색에 사용. 한국어 행정문서가 주 코퍼스 — 한국어 특화 모델이 1차 후보. 자체 호스팅 vs API 분기.

### 후보 비교

| 항목 | BGE-M3 (1순위 추천) | OpenAI text-embedding-3-large | Solar embedding-1-large | Voyage / Cohere |
|---|---|---|---|---|
| 한국어 성능 | 우수 (multilingual 강점) | 중상 | 우수 (한국어 특화) | 중 |
| 차원·인덱스 비용 | 1024차원 | 3072차원 (저장 비용 ↑) | 4096차원 | 1024~1536 |
| 호스팅 | 자체 가능 (Apache 2.0) | API 전용 | API 전용 (국내) | API 전용 |
| 단가 (1M 토큰) | 무료 (자체) / $0.10~ 호스팅 | $0.13 | $0.10 | $0.12 |
| 검색 정확도 (KO) | retrieval bench 상위 | 양호 | 상위 | 중 |
| 모델 교체 비용 | 자체 호스팅이라 자유 | API 종속 | API 종속 | API 종속 |
| 다국어 지원 | 100+ | 100+ | 한국어 중심 | 영어 중심 |

### 추천: **BGE-M3 자체 호스팅**

**근거**:
- 한국어 retrieval 성능이 OpenAI 수준 또는 그 이상이면서 차원이 작아 인덱스·검색 비용 절약
- 자체 호스팅으로 PII가 외부로 나가지 않음 (개인정보·기업식별정보 보호)
- 모델 업그레이드·세분화(분쟁/인허가 도메인별 파인튜닝) 자유로움
- 1차 출시 후 데이터 누적되면 도메인 fine-tune으로 정확도 추가 상승 가능

### 보충 의견
- 자체 호스팅 부담 우려 시 1차는 OpenAI text-embedding-3-large API로 시작 → 데이터 누적 후 BGE-M3로 마이그레이션 옵션 열어둠. 단 마이그레이션은 전체 재인덱싱 동반.
- KURE-v1 같은 한국어 retrieval 특화 모델도 후보 — BGE-M3과 정확도 비교 후 채택 검토 가능.

### 결정 필요
- [ ] BGE-M3 자체 호스팅 또는 OpenAI API 시작 (마이그레이션 옵션 열어둠) 중 어느 쪽?
- [ ] GPU 호스팅 환경 결정 (D9와 연동)

---

## D3. 벡터 DB

### 컨텍스트
DA3 인덱스 + 사용자별 personal RAG + 사용자 골격 라이브러리 검색. 접근 권한 필터(public/shared/personal)가 사전 필터로 강제되어야 함. 1차는 수천~수만 문서 규모.

### 후보 비교

| 항목 | pgvector (1순위 추천) | Qdrant | Weaviate | Pinecone |
|---|---|---|---|---|
| 운영 부담 | 기존 Postgres에 확장 추가만 | 별도 서비스 운영 | 별도 서비스 운영 | SaaS (운영 0) |
| 한국 호스팅 | AWS Seoul·국내 클라우드 가능 | 자체 호스팅 | 자체 호스팅 | US/EU 위주 (데이터 주권 우려) |
| 메타데이터 필터 | SQL JOIN 자유 (강점) | 우수 | 우수 | 중상 |
| 하이브리드 검색 | FTS + 벡터 (Postgres 내) | 내장 BM25 | 내장 BM25 | 외부 BM25 결합 |
| HNSW 성능 | 좋음 (~수십만 OK) | 매우 우수 | 매우 우수 | 매우 우수 |
| 비용 | RDS 인스턴스 ~$50/월 시작 | self-host 무료 / cloud $100+ | self-host 무료 / cloud $100+ | $70+ 시작 |
| 트랜잭션·관계 | Postgres 그대로 | 별도 | 별도 | 별도 |
| 마이그레이션 비용 | 표준 SQL 백업 | 별도 도구 | 별도 도구 | export API |

### 추천: **pgvector**

**근거**:
- DA2 사용자 라이브러리·DA1 공식 양식 메타데이터가 관계형이 자연스러움 → 같은 Postgres에 두면 JOIN 자유
- 접근 권한 필터(`access_scope = 'personal' AND owner = $1`)를 SQL로 우선 적용 — 권한 누락 위험 낮음
- 운영 부담 작고 백업·복구 표준 (Postgres 생태계)
- 수십만 문서 규모까지는 성능 충분, 이를 넘어가면 Qdrant로 마이그레이션 옵션

### 보충 의견
- 임베딩 차원이 BGE-M3(1024)면 pgvector 한계 안에서 안전. OpenAI 3072차원이면 인덱스 크기 부담 — D2 결정과 연동.
- 검색 latency가 100ms 넘는 시점에 Qdrant 분리 검토. 그 전까지는 같은 DB 안에 두는 게 운영 단순.

### 결정 필요
- [ ] pgvector 채택?
- [ ] Postgres 인스턴스 타입·메모리 (D9와 연동)

---

## D4. 백엔드 언어/프레임워크

### 컨텍스트
런타임 에이전트 8개 + 오케스트레이터 + SSE 스트리밍 + 외부 API 통합. LLM·RAG 생태계가 Python 중심이라는 점이 강력한 제약.

### 후보 비교

| 항목 | Python + FastAPI (1순위 추천) | TypeScript + Hono/NestJS | Go + Gin |
|---|---|---|---|
| LLM 생태계 (Claude SDK, LangGraph, LlamaIndex) | 가장 풍부 | 충분 (Anthropic SDK 공식) | 빈약 (직접 HTTP) |
| 한국어 NLP 도구 | KoNLPy, kiwi, soynlp | 적음 | 적음 |
| 임베딩·벡터 처리 | sentence-transformers, FAISS 등 풍부 | 의존 적음 (외부 호출) | 의존 적음 |
| 첨부 파서 (PDF/HWP) | PyMuPDF, pdfplumber, pyhwp 풍부 | 부족 (특히 HWP) | 부족 |
| SSE 스트리밍 | FastAPI native | Hono·Express 충분 | 충분 |
| 동시성 | async/await, uvicorn | event loop | goroutine (강점) |
| 타입 안전 | Pydantic v2 | TS native | 컴파일 타임 |
| 운영 부담 | 표준 | 표준 | 단일 바이너리 (장점) |
| 풀스택 통일 | 프론트와 분리 | 프론트와 동일 언어 (장점) | 프론트와 분리 |

### 추천: **Python + FastAPI + Pydantic v2**

**근거**:
- DA4 첨부 파서가 한국어 행정문서의 핵심인데 HWP·HWPX 처리 라이브러리가 Python에 가장 성숙
- LLM 어댑터(공식 SDK·재시도·토큰 회계)·LangGraph 패턴이 검증됨
- Pydantic으로 `SessionState` 등 인터페이스를 코드로 직역 가능 — `01-agents.md`의 TS 의사코드와 1:1 매핑
- FastAPI의 SSE 처리는 표준, async 흐름이 오케스트레이터에 적합

### 보충 의견
- 프론트와 다른 언어가 단점이지만, 인터페이스 스키마는 JSON Schema·OpenAPI로 양쪽 생성 가능 → 실질적 마찰 낮음
- 비동기 워커(#8 학습기, 코퍼스 수집)는 같은 Python 코드로 Celery·RQ 같은 큐로 분리 자연스러움

### 결정 필요
- [ ] Python + FastAPI 채택?
- [ ] 비동기 워커 큐 (Celery / RQ / Dramatiq) — Phase B3 진입 시 결정 가능

---

## D5. 프론트엔드 프레임워크

### 컨텍스트
3패널 워크벤치, Progressive form, SSE 스트리밍 클라이언트, 인라인 편집·키보드 단축키. 상태 머신 복잡. SSR 필요성은 낮음(앱 성격).

### 후보 비교

| 항목 | Next.js (App Router) | Vite + React SPA (1순위 추천) | SvelteKit | SolidStart |
|---|---|---|---|---|
| 학습·생태계 | React 풍부 | React 풍부 | Svelte 충분 | 신생 |
| 상태 관리 (워크벤치) | Zustand·Jotai·Redux | 동일 | 내장 stores | signals 내장 |
| 컴포넌트 라이브러리 | shadcn/ui·MUI·Radix 풍부 | 동일 | Skeleton·Flowbite-svelte | 적음 |
| SSR/SSG 필요성 | 강점이지만 본 앱에 불필요 | 없음 (앱 성격에 맞음) | 강점이지만 본 앱에 불필요 | 강점 |
| 빌드·개발 속도 | webpack·Turbopack | Vite (가장 빠름) | Vite | Vite |
| SSE 처리 | 표준 fetch + ReadableStream | 동일 | 동일 | 동일 |
| 인증·라우팅 | 풀스택 통합 (장점이나 분리도 가능) | 분리 명확 | 풀스택 통합 | 분리 |
| 백엔드와 분리 | 가능 (API Routes 안 써도 됨) | 명확 분리 | 가능 | 명확 분리 |

### 추천: **Vite + React (SPA)**

**근거**:
- autodoxc는 SaaS 워크벤치 — SSR/SSG 가치 낮음. SEO 대상 페이지는 마케팅 사이트로 분리 (별도 정적)
- 백엔드가 Python(D4)이라 Next.js의 풀스택 장점은 안 쓰임 → 단순 SPA가 깔끔
- 개발 속도(Vite HMR)와 디버깅이 가장 빠름
- React 생태계의 shadcn/ui + Radix Primitives로 접근성·키보드 단축키 표준 가까이 구현 가능

### 보충 의견
- 상태 관리: Zustand 권장 (서비스가 클라이언트 상태가 깊고, redux 보일러플레이트 불필요)
- 스트리밍: native fetch + ReadableStream (Server-Sent Events). 라이브러리 의존 최소
- 추후 마케팅·랜딩 페이지가 필요해지면 Next.js·Astro 별도 사이트로

### 결정 필요
- [ ] Vite + React SPA 채택?
- [ ] 컴포넌트 라이브러리: shadcn/ui + Radix Primitives 권장 — 동의?

---

## D6. HWP 파싱 전략

### 컨텍스트
DA4의 핵심 난제. 한국 행정문서 양식이 HWP·HWPX로 다수 배포됨. 자체 파싱 안정성이 낮은 영역.

### 후보 비교

| 항목 | 자체 (pyhwp/hwp5) | HWPX 변환 우회 (1순위 추천 — 단계적) | 외부 변환 서비스 | Hancom Office API |
|---|---|---|---|---|
| HWPX (XML 표준) | 우수 (직접 파싱) | 우수 | 우수 | 미지원 또는 부분 |
| HWP (구버전 바이너리) | 실패율 높음 (구조 복잡) | HWP→HWPX 변환 동반 | 안정 | 안정 (라이선스) |
| 비용 | 0 | 0 (오픈소스 변환기 활용) | 호출당 과금 | 라이선스 비용 |
| 안정성 | 30~60% | HWPX는 ~95%, HWP는 변환 의존 | 95%+ | 95%+ |
| 의존성 | Python only | 변환기(외부 바이너리·Wasm) | 외부 서비스 의존 | 한컴 API 의존 |
| 데이터 주권 | 자체 | 자체 | 외부 전송 우려 | 한컴 서버 |

### 추천: **단계적 — HWPX 우선 + HWP는 hwp5 1차 → 변환기 fallback**

**전략**:
1. `.hwpx` (XML 표준 포맷): 자체 파서로 직접 처리 — 가장 안정
2. `.hwp` (구버전):
   - 1차 시도: `hwp5` 또는 `pyhwp` 라이브러리
   - 실패 시 fallback: HWP→HWPX 또는 HWP→DOCX 변환기 호출 (오픈소스 hwp-converter, libreoffice 등)
   - 사용자에게 "변환 결과 확인" 알림 표시
3. 실패율 모니터링 → 30% 이상이면 외부 변환 서비스 또는 한컴 API 도입 검토 (Phase B3 시점)

**근거**:
- HWPX가 표준이 되어가는 추세 — 시간이 도와줌
- 외부 서비스 의존은 PII 문제(첨부 양식에 사용자 데이터 포함 가능) — 자체 또는 자체 변환기 우선
- 라이선스 비용을 1차에서 피하고, 안정성이 충분치 않다고 판단되면 도입 검토

### 보충 의견
- HWP/HWPX는 사용자 양식 첨부 1차 케이스. DA1 공식 양식 코퍼스는 PDF·DOCX 우선 큐레이션으로 의존 분산
- 사용자가 양식 파싱 결과를 확인하고 수정할 수 있는 UI(`03-ui-model §2`) 있으니, 100% 파싱은 불필요. 골격 추출 정확도만 합당하면 됨

### 결정 필요
- [ ] 단계적 전략 채택?
- [ ] HWP 변환 백업으로 LibreOffice headless 변환 도입 OK? (호스팅 환경에 LibreOffice 설치 필요)

---

## D7. 외부 법령 API

### 컨텍스트
#5 EvidenceRetriever의 핵심 소스. 법령 인용은 행정문서 신뢰성의 근간 — 권위 있는 출처 필요.

### 후보 비교

| 항목 | 국가법령정보센터 OpenAPI (1순위 추천) | 자체 미러 (크롤 + 인덱스) | 종합법률정보 / 케이스노트 (병행) |
|---|---|---|---|
| 권위 | 정부 공식 | 정부 데이터 복제 | 민간 (판례 강점) |
| 비용 | 무료 (API 키) | 0 (초기) + 운영 부담 | 라이선스 비용 |
| 커버리지 | 법령·시행령·시행규칙·별표 | 동일 | 판례·해석례 추가 |
| 업데이트 즉시성 | 즉시 (정부 갱신 시) | 크롤 주기 의존 | 가입 모델 |
| Rate limit | 표준 (캐시 필수) | 자체 제어 | 라이선스에 따라 |
| 의존 리스크 | API 변경·중단 위험 | 자체 운영 부담 | 라이선스 의존 |
| 판례 | 별도 (법령만) | 별도 | 강점 |

### 추천: **국가법령정보센터 OpenAPI + 자체 캐시 + DA3 이중화** (판례는 Phase B3에 추가 결정)

**전략**:
- 1차: 국가법령정보센터 OpenAPI를 EvidenceRetriever의 `statute` 채널로 연결
- 캐시 정책: `02-data-assets §EXT` 명세대로 — 법령 TTL 7일, 결과는 DA3에도 인덱싱
- API 변경·장애 대비 → DA3 자체 RAG가 1차 폴백
- 판례는 Phase B3 진입 시 외부 라이선스(케이스노트 등) 검토. 1차에서는 LLM 일반 지식 + RAG로 진행, "참고" 수준 표기

**근거**:
- 행정문서에서 법령 인용은 정확성·권위가 1순위 — 정부 공식 소스가 정답
- 무료 + Rate limit 합리적 + 표준 형식
- 법령 개정 즉시 반영 (DA1 공식 양식 갱신 트리거)

### 보충 의견
- 판례 부재의 영향: 분쟁/구제 도메인(내용증명·행정심판)에서 판례 인용 약화. Phase B3에서 KASB 같은 공개 판례 RAG로 보완하거나 케이스노트 도입

### 결정 필요
- [ ] 국가법령정보센터 OpenAPI 인증키 발급 신청 (M4 위임 가능)?
- [ ] 판례 소스는 Phase B3 진입 시 재결정 OK?

---

## D8. 인증·세션

### 컨텍스트
DA2 personal/shared 2계층 + 행정사 사무소 단위 권한 + PII 데이터 다룸. 멀티유저 + 조직 모델 필요.

### 후보 비교

| 항목 | Clerk (1순위 추천 — 초기 속도) | Auth0 | 자체 (JWT + DB) | Supabase Auth |
|---|---|---|---|---|
| 조직(Organizations) 모델 | 내장 (사무소 단위에 최적) | 내장 | 자체 설계 | 부분 |
| 한국 호스팅·리전 | US 위주 (데이터 처리 위치 명시 필요) | US/EU | 자체 (장점) | EU |
| 단가 (MAU) | 5K까지 무료, 이후 $25/월부터 | 25K까지 무료, 이후 $240+ | 인스턴스 비용만 | 50K 무료 |
| SSO·MFA·소셜 | 표준 | 표준 | 자체 구현 부담 | 표준 |
| 한국 SMS/카카오 로그인 | 카카오 가능 (커스텀) | 가능 (커스텀) | 자유 | 가능 |
| 마이그레이션 비용 (탈출) | 사용자 export 가능 | 동일 | 자유 | 자유 |
| 컴플라이언스 (개인정보보호법) | 데이터 처리 계약 확인 필요 | 동일 | 자체 책임 (제어) | 동일 |

### 추천: **Clerk (1차 출시) + 자체 전환 옵션 열어둠**

**근거**:
- 사무소(Organization) 모델이 내장 — DA2의 `owner.office_id` 권한 모델을 빠르게 구현
- 인증 UX(소셜 로그인·MFA·세션 관리)를 자체 구현하지 않고 1차 출시 가능
- 5K MAU까지 무료 — 초기 콜드스타트에 비용 0
- 마이그레이션 경로(사용자 export)가 있어 락인 위험 제한적

### 보충 의견
- **데이터 주권 우려**: 행정 PII 다루는 점에서 Clerk의 한국 사용자 데이터 처리 위치를 명시 계약으로 확인 필수
- 컴플라이언스 부담이 크다고 판단되면 즉시 자체 구현으로 전환 — JWT + Postgres `users`·`offices`·`memberships` 테이블 단순 설계로 1주 내 가능
- 카카오·네이버 로그인: 한국 사용자 친화. Clerk 또는 자체 구현 모두 OAuth 추가 가능

### 결정 필요
- [ ] Clerk 1차 채택, 데이터 처리 계약 확인 동반?
- [ ] 또는 자체 구현으로 1차 가는 게 컴플라이언스상 안전한지 — 사용자 판단
- [ ] 소셜 로그인 1차 범위 (이메일 + 카카오?)

---

## D9. 호스팅

### 컨텍스트
PII·기업 식별정보 처리. 한국 개인정보보호법·전자정부 보안 가이드 고려. 콜드스타트 트래픽 작고 운영 안정성·데이터 주권 가중치 큼.

### 후보 비교

| 항목 | AWS Seoul (1순위 추천) | GCP asia-northeast3 (Seoul) | NCP (네이버 클라우드) | KT Cloud / NHN Cloud |
|---|---|---|---|---|
| 한국 리전 (데이터 주권) | Seoul 리전 | Seoul 리전 | 국내 (장점) | 국내 (장점) |
| LLM 추가 옵션 | Bedrock (Claude·Llama·Titan) | Vertex AI (Gemini) | HyperCLOVA X | 외부 LLM 통합 |
| Postgres + pgvector | RDS·Aurora (관리형) | Cloud SQL (관리형) | DBaaS | 동일 |
| GPU (BGE-M3 호스팅) | g4dn·g5 인스턴스 | 동일 | 가능 | 가능 |
| 컨테이너·서버리스 | ECS·Fargate·Lambda 풍부 | Cloud Run·GKE 풍부 | 컨테이너 서비스 | 동일 |
| 관측성 (로그·메트릭) | CloudWatch·X-Ray | Cloud Logging·Trace | NCP 모니터링 | 동일 |
| 비용 (소규모 시작) | RDS t3.small + Fargate 작은 단위로 $150~/월 | 유사 | 유사 또는 낮음 | 유사 |
| 한국 행정 컴플라이언스 (CSAP 등) | 보유 | 보유 | 보유 (강점) | 보유 (강점) |
| 운영 노하우·생태계 | 가장 풍부 | 풍부 | 한국어 친화 | 한국어 친화 |

### 추천: **AWS Seoul (개발·1차 출시) + 한국 클라우드(NCP/KT/NHN) 운영 단계 평가**

**전략**:
1. Phase B0~B3 (개발·내부 시험): AWS Seoul. 관리형 서비스·생태계·운영 노하우의 장점이 큼
2. Phase B4 출시 직전: 행정사·실무자 대상 + PII 비중을 보고 CSAP 인증 한국 클라우드(NCP/KT/NHN) 마이그레이션 평가
3. 마이그레이션 비용 낮추기 위해 컨테이너(Docker) + Terraform IaC로 이식성 확보

**근거**:
- AWS Seoul도 한국 리전이라 1차 컴플라이언스는 통과 가능
- 개발·디버깅·도구 생태계에서 AWS의 강점이 1년 동안 큰 가치
- 운영 단계에 공공기관 거래·민감 사용자(행정사) 확장 시 한국 클라우드의 CSAP 인증이 정책적 advantage — 마이그레이션 보험

### 보충 의견
- BGE-M3 호스팅 GPU 비용이 부담이면 1차는 OpenAI 임베딩 API로 시작하고 데이터 누적 후 자체 호스팅 전환 (D2 보충 의견과 일치)
- 비밀·키 관리는 AWS Secrets Manager 또는 동등 서비스 사용 — 환경변수 평문 금지

### 결정 필요
- [ ] AWS Seoul 1차 채택 + Terraform IaC 동반?
- [ ] 운영 단계 한국 클라우드 마이그레이션 옵션 합의?
- [ ] BGE-M3 GPU 호스팅 vs OpenAI 임베딩 1차 API (D2와 연동)

---

## 결정 요약 (한눈에)

| # | 항목 | 추천 | 결정 | ADR |
|---|---|---|---|---|
| D1 | LLM 공급자 | Anthropic Claude 티어 분리 (Opus/Sonnet/Haiku) | ✅ Accepted | [0001](../../adr/0001-llm-provider-anthropic-tiered.md) |
| D2 | 임베딩 모델 | 콜드스타트 OpenAI API → Phase B2 BGE-M3 자체 호스팅 | ✅ Accepted | [0002](../../adr/0002-embedding-bge-m3.md) |
| D3 | 벡터 DB | pgvector | ✅ Accepted | [0003](../../adr/0003-vector-db-pgvector.md) |
| D4 | 백엔드 | Python + FastAPI + Pydantic v2 | ✅ Accepted | [0004](../../adr/0004-backend-python-fastapi.md) |
| D5 | 프론트엔드 | Vite + React (SPA) + shadcn/ui | ✅ Accepted | [0005](../../adr/0005-frontend-vite-react-spa.md) |
| D6 | HWP 파싱 | 단계적 (HWPX 직접 / HWP는 hwp5 + LibreOffice fallback) | ✅ Accepted | [0006](../../adr/0006-hwp-parsing-staged.md) |
| D7 | 법령 API | 국가법령정보센터 OpenAPI + 자체 캐시 + DA3 이중화 | ✅ Accepted | [0007](../../adr/0007-law-api-national-law-center.md) |
| D8 | 인증 | Clerk 1차 (자체 전환 옵션 열어둠) | ✅ Accepted | [0008](../../adr/0008-auth-clerk-with-fallback.md) |
| D9 | 호스팅 | AWS Seoul (1차) → 한국 클라우드 운영 단계 평가 | ✅ Accepted | [0009](../../adr/0009-hosting-aws-seoul-staged.md) |

## 결정 후 다음 단계

1. 결정 받은 항목별로 **ADR 001~009** 분리 작성 (`docs/adr/`)
2. lead-architect 통합 보고 → Phase B0 진입 신호
3. 각 owner에게 결정 통보 (SendMessage)
   - D1, D4 → backend-engineer (LLM 어댑터·언어 시작)
   - D2, D3 → data-rag-engineer (벡터 DB·임베딩 인프라)
   - D5 → frontend-engineer (프로젝트 부트스트랩)
   - D6 → data-rag-engineer (파서 우선순위)
   - D7 → data-rag-engineer (API 키 신청)
   - D8 → backend-engineer + lead-architect (조직 모델·세션)
   - D9 → lead-architect (인프라 IaC 구성)
4. CLAUDE.md 변경 이력에 "B0 진입 + 외부 의존성 결정" 한 줄 추가

## 보류·연동 가능 결정 (참고)

- **비용 임계치 (token budget·MAU)**: D1·D8 채택 후 1주 운영 시뮬레이션 후 결정
- **모니터링 도구**: Sentry·Datadog 또는 자체 — Phase B2 진입 시
- **CI/CD**: GitHub Actions + Terraform — Phase B0 진입 후 표준 결정 (사용자 결정 항목 아님)
