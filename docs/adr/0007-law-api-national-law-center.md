# ADR 0007: 법령 API — 국가법령정보센터 OpenAPI + 자체 캐시 + DA3 이중화

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

#5 EvidenceRetriever의 핵심 외부 소스. 행정문서에서 법령 인용 정확성은 신뢰성의 근간. 권위 있는 공식 출처 필요 + 호출 안정성·비용 관리 필요.

## 결정

**국가법령정보센터 OpenAPI** 1차 채택.

**구체 정책**:
- 인증키: M4가 [국가법령정보센터](https://open.law.go.kr) 가입·신청
- 호출 패턴: 캐시 우선 (`02-data-assets §EXT`)
- TTL: 법령 7일, 조문 7일, 시행규칙 7일
- 캐시 키 표준화: `law:{normalized_query}:{filters_hash}`
- 결과는 DA3 RAG 인덱스에도 후속 인덱싱 — 재사용·오프라인 fallback
- Rate limit 도달 시: 캐시 우선 → 백오프 → 같은 쿼리 묶음 처리

**판례·해석례는 별도 결정 (Phase B3)**:
- 1차에서는 LLM 일반 지식 + DA3 RAG로 진행
- 사용자에게 "참고 — 공식 인용 보강 필요" 표기
- Phase B3 진입 시 케이스노트·종합법률정보 등 외부 라이선스 도입 검토 — 별도 ADR

## 대안

- **자체 미러 (크롤)**: 공식 데이터 복제 부담 + 갱신 즉시성 떨어짐
- **종합법률정보 / 케이스노트**: 판례 강점이나 법령 자체는 동일하고 라이선스 비용 발생
- **LLM 일반 지식만**: 할루시네이션 위험 — 법령 인용에 부적합

## 결과

**영향 모듈**:
- `src/data/external/law_api.py` — 국가법령정보센터 클라이언트
- `src/data/external/cache.py` — Redis 또는 Postgres `external_cache` 테이블
- `src/data/rag/indexer.py` — 캐시 hit 결과를 DA3에도 인덱싱

**환경 변수**:
- `LAW_API_KEY` — 인증키 (Secrets Manager에 저장)
- `LAW_API_BASE_URL` — `https://www.law.go.kr/DRF/lawService.do` 또는 동등

**폴백 체인**:
1. 캐시 hit → 즉시 반환
2. 캐시 miss → API 호출 → 캐시·DA3 동시 저장
3. API 실패 → DA3 자체 검색 fallback
4. DA3도 0건 → LLM 일반 지식 사용 + "출처 미확인" 명시

**측정·운영**:
- 캐시 적중률 (목표: 70%+)
- API 호출 실패율
- 인용 정확성 회귀 (M6 fixture)

**Phase B1 진입 시점**:
- M4가 API 키 신청 완료
- 기본 호출·캐시·폴백 구현
- M6가 법령 인용 회귀 fixture 작성

**판례 도입 결정 시점**: Phase B3 진입 시 사용자 에스컬레이션 — 비용·라이선스 영향 큼.
