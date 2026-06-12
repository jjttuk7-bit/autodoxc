# ADR 0009: 호스팅 — AWS Seoul (개발·1차 출시) + 운영 단계 한국 클라우드 평가

**상태**: Accepted
**날짜**: 2026-06-12
**결정자**: lead-architect, with user/PM

## 맥락

PII·기업 식별정보 처리 — 개인정보보호법·전자정부 보안 가이드 준수 필요. 1차 콜드스타트 트래픽 작고 운영 부담 최소화 가치. 행정사·실무자 대상 확장 시 CSAP 인증 가치 부각.

## 결정

**2단계 호스팅 전략**:

### Phase B0~B3 (개발·내부 시험): AWS Seoul (`ap-northeast-2`)

**컴포넌트 매핑**:
| 자산 | AWS 서비스 |
|---|---|
| 컨테이너 런타임 | ECS Fargate (백엔드 + 워커) |
| 정적 호스팅 | CloudFront + S3 (프론트엔드 SPA) |
| Postgres + pgvector | RDS Postgres 16+ (t3.small 시작) |
| 캐시·큐 | ElastiCache Redis (또는 운영 비용 줄이려면 Postgres LISTEN/NOTIFY) |
| 비밀 관리 | Secrets Manager |
| 객체 저장 | S3 (원본 첨부 파일·DA1 원본) |
| 관측성 | CloudWatch + X-Ray |
| 외부 변환기 (HWP) | LibreOffice가 포함된 Docker 이미지 (별도 Fargate 태스크) |
| BGE-M3 GPU (Phase B2 진입 시) | g5.xlarge 또는 g4dn.xlarge |
| LLM | Anthropic API 직접 (Bedrock 옵션 보유) |

**비용 추정 (월, 콜드스타트)**: $150~250
- RDS t3.small: ~$30
- Fargate 작은 단위: ~$50
- CloudFront/S3: ~$10
- ElastiCache 최소: ~$15
- 기타: ~$50

### Phase B4 진입 시: 한국 클라우드(NCP/KT Cloud/NHN Cloud) 마이그레이션 평가

**평가 트리거**:
- 공공기관·대형 사무소 고객 출현 — CSAP 요구
- PII 정책 강화 — 한국 클라우드 가치 상승
- 이용자 수·트래픽 증가로 운영 비용 비교 가치

**마이그레이션 비용 최소화**:
- 컨테이너(Docker)로 모든 워크로드 패키징
- Terraform IaC로 인프라 정의 — 클라우드 추상화 가능한 부분 분리
- 데이터 마이그레이션: Postgres 백업·복구 표준 절차

## 대안

- **AWS Seoul만 (마이그레이션 옵션 없음)**: 공공·민감 사용자 확장 시 정책적 제약
- **한국 클라우드 첫날부터**: AWS 도구·생태계 가치를 콜드스타트에 잃음
- **GCP asia-northeast3**: AWS와 유사하나 LLM(Bedrock 대안 Vertex Gemini)·생태계 차이

## 결과

**영향 모듈**:
- `infra/terraform/` — IaC (Phase B0 시점 작성)
- `Dockerfile` (백엔드·워커·변환기)
- `docker-compose.yml` (로컬 개발)
- CI/CD: GitHub Actions → Terraform plan/apply

**Terraform 구조**:
```
infra/terraform/
├── envs/
│   ├── dev/
│   ├── staging/
│   └── prod/
├── modules/
│   ├── network/
│   ├── compute/
│   ├── database/
│   ├── storage/
│   └── observability/
└── README.md
```

**보안·컴플라이언스 1차 체크리스트**:
- [ ] VPC 격리 (private subnet에 DB·워커)
- [ ] Secrets Manager로 모든 키 관리 (env 평문 0)
- [ ] CloudTrail 로깅
- [ ] RDS 암호화 (저장·전송)
- [ ] S3 SSE-KMS
- [ ] WAF (CloudFront 앞)
- [ ] 정기 백업 (RDS 자동·S3 cross-region)

**Phase B4 평가 항목**:
1. CSAP 인증 사용자 요구 발생 시점
2. 한국 클라우드 비용 비교 (1년 운영 데이터 기반)
3. 마이그레이션 비용·다운타임 추정
4. 결정 → 별도 ADR

**회귀 검증**: M6 + 사용자가 부하 테스트 1회 (Phase B4 진입 직전).

**연동 결정**:
- D2: BGE-M3 호스팅 시 GPU 인스턴스 비용 IaC에 반영
- D7: 법령 API 호출은 NAT Gateway 통해 outbound (캐시 적중률로 비용 관리)
- D8: Clerk webhook은 ALB → ECS 경로
