# autodoxc IaC (Terraform)

ADR 0009 (AWS Seoul → 운영 단계 한국 클라우드 평가)의 1차 구현 골격.

## 구조

```
infra/terraform/
├── envs/
│   ├── dev/        # 개발 환경 (이 디렉토리만 우선 작성)
│   ├── staging/    # TBD
│   └── prod/       # TBD
└── modules/
    ├── network/    # VPC + subnets + IGW + NAT
    ├── compute/    # ECS Fargate + ALB
    ├── database/   # RDS Postgres + pgvector
    └── storage/    # S3 (원본 첨부·DA1 원본) + CloudFront
```

## 사용

```pwsh
cd infra/terraform/envs/dev
terraform init
terraform plan
terraform apply
```

> 이 골격은 실제 배포 가능한 완전 IaC가 아닌 **모듈 wire-up 청사진**.
> B0-7 단계에서 골격만 잡고, 실제 리소스 정의 + 보안 그룹 + IAM 정책은 Phase B4 진입 시 보강.

## 사전 요구

- Terraform 1.9+
- AWS CLI 구성 (`aws configure`)
- 한국 리전 활성화 (`ap-northeast-2`)
- 비밀: Secrets Manager에 `autodoxc/dev/*` prefix로 저장
  - `autodoxc/dev/anthropic_api_key`
  - `autodoxc/dev/clerk_secret_key`
  - `autodoxc/dev/openai_api_key`
  - `autodoxc/dev/law_api_key`
  - `autodoxc/dev/db_password`

## State

State backend는 S3 + DynamoDB lock — 별도 부트스트랩 스크립트(미작성)로 한 번만 생성 후 모든 env가 공유.
