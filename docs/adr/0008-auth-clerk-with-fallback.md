# ADR 0008: 인증·세션 — Clerk (1차) + 자체 전환 옵션

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

DA2 personal/shared 2계층 + 행정사 사무소 단위 권한. PII·기업 식별정보 다룸. 1차 출시 속도와 컴플라이언스 균형 필요.

## 결정

**Clerk 1차 채택, 자체 구현 전환 옵션 유지**.

**구체 정책**:
- Clerk Organizations 모델로 사무소(office) 표현 — DA2 라이브러리의 `owner.office_id`와 1:1 매핑
- 인증 방식 1차 범위: 이메일 + 카카오 OAuth (한국 사용자 친화)
- JWT 검증은 백엔드 미들웨어 (FastAPI Depends)
- 사용자·사무소 메타데이터만 자체 Postgres에 복제 (Clerk webhook으로 동기화) — 락인 방지
- PII 데이터(행정문서 본문)는 Clerk에 절대 전달하지 않음 — 자체 DB만

**전환 트리거 (자체 구현으로)**:
1. 데이터 처리 위치 컴플라이언스 검토 실패
2. MAU 5K 초과 + 운영 비용 부담 (월 $100+)
3. 카카오·네이버 외 추가 한국 소셜 로그인 필요 (Clerk 커스텀 비용)

**전환 비용 추정**:
- 자체 구현 (JWT + Postgres): 1주 — 사용자 export → 자체 테이블 인서트 → JWT 발급 로직
- 사용자 비밀번호: Clerk export는 hash만 가능 — 사용자에 비밀번호 재설정 안내

## 대안

- **Auth0**: 기능 동등, 가격대 높음, 조직 모델 동급
- **자체 (JWT + DB) 첫날부터**: 컴플라이언스 강점 + 출시 1~2주 지연
- **Supabase Auth**: EU 호스팅 — 데이터 주권 우려

## 결과

**영향 모듈**:
- `src/backend/auth/clerk_middleware.py` — JWT 검증
- `src/backend/auth/webhook.py` — Clerk 이벤트 동기화
- `src/backend/models/user.py`, `office.py`, `membership.py` — 자체 메타데이터
- `src/frontend/auth/` — Clerk React SDK

**환경 변수**:
- `CLERK_PUBLISHABLE_KEY` (프론트)
- `CLERK_SECRET_KEY` (백엔드)
- `CLERK_WEBHOOK_SECRET`

**권한 모델 (DA2 통합)**:
```
- 사용자 A가 사무소 X 소속 → A는 자기 personal + 사무소 X의 shared 모두 read/write
- 사용자 B가 사무소 X 소속 → B는 자기 personal + 사무소 X의 shared 모두 read/write
- 사무소 간 격리: A는 사무소 Y의 데이터 접근 불가
- 공용 라이브러리(`shared` 승격분): 모든 사용자 read, 시스템 관리자만 write
```

**컴플라이언스 액션**:
- Clerk와 데이터 처리 계약(DPA) 확인 — 사용자 데이터 보관 위치·기간 명시
- 한국 사용자 데이터 처리 위치 자료 요청
- 개인정보보호법 14조(국외이전) 안내 동의 절차 — UI에 포함

**회귀 검증**:
- M6가 사무소 간 격리 회귀 (`tests/integration/auth-tenant-isolation`)
- DA2 권한 누수 fixture (다른 사무소 데이터 검색 결과 노출 X)

**모니터링**:
- Clerk 응답 시간·실패율
- MAU 추적 — $25/월 임계치 도달 시 알림
- 인증 실패율 (브루트 포스 탐지)
