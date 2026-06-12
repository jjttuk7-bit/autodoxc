# ADR 0006: HWP 파싱 전략 — 단계적 (HWPX 우선 + HWP는 hwp5 → 변환기 fallback)

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

DA4 첨부 양식 파서의 최대 난제. 한국 행정문서가 HWP·HWPX로 다수 배포됨. 자체 파싱 안정성은 낮으나 외부 의존은 PII 노출·비용 우려.

## 결정

**3단계 폴백 체인**:

### 1차: HWPX (XML 표준)
- 직접 파싱 (`xml.etree` 또는 `lxml`)
- 표준 XML 구조라 안정성 95%+
- HWPX는 OWPML 표준 — 한컴이 공개

### 2차: HWP (구버전 바이너리)
- 1차 시도: `hwp5` Python 라이브러리 (또는 `pyhwp`)
- 결과 confidence를 측정 (텍스트 추출률, 표 구조 보존 등)
- confidence < 0.7이면 3차로 강등

### 3차: 변환기 폴백 (HWP → HWPX 또는 HWP → DOCX)
- **LibreOffice headless** 변환 (`libreoffice --headless --convert-to docx`)
- 변환된 DOCX/HWPX를 다시 1차 파서로 처리
- 변환 자체가 실패하면 사용자에게 명시적 에러: "양식 파싱 실패. 텍스트로 다시 시도하시겠어요?"

### 사용자 노출
- 모든 파싱 결과는 `ParseResult.warnings`로 신뢰도 표시
- 캔버스에 골격 보여줄 때 "양식 파싱 부분적 — 확인 부탁드립니다" 표기 (`03-ui-model §1.3`)

## 대안

- **자체만**: 30~60% 안정성 — 1차 출시에 부족
- **외부 변환 서비스 (유료)**: PII 외부 전송 우려 + 비용
- **Hancom Office API**: 라이선스 비용 + 한컴 서버 의존
- **HWP 미지원**: HWP가 한국 행정문서 핵심 포맷 — 미지원은 시장 적합성 손실

## 결과

**영향 모듈**:
- `src/parsers/hwp.py`
- `src/parsers/hwpx.py`
- `src/parsers/converters/libreoffice.py` (헬퍼)
- `src/parsers/pipeline.py` (체인 오케스트레이션)

**호스팅 영향 (D9 연동)**:
- AWS Seoul 배포 시 LibreOffice 설치 동반 (Docker 이미지에 포함)
- 변환 호출은 격리된 worker 또는 별도 컨테이너에서 실행 (메인 API와 분리)
- 변환 평균 시간 5~10초 — 사용자에게 진행 알림

**측정·운영**:
- HWP 파싱 실패율 메트릭 (`02-data-assets §EXT` 텔레메트리 일부)
- 실패율 30% 초과 시 ADR supersede — 외부 변환 서비스 또는 한컴 API 도입 검토 (Phase B3 진입 후)

**우선순위 (Phase B2 작업)**:
1. `.docx` (가장 안정적, 우선 검증)
2. `.pdf` (텍스트 레이어)
3. `.hwpx`
4. `.hwp` + LibreOffice fallback
5. `.pdf` (스캔본) — OCR
6. 이미지

**회귀 검증**: M6가 도메인 양식 fixture 30~50개 수집 (M5 큐레이션 협조), 포맷별 파싱 성공률 회귀.
