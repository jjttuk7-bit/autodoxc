# 로컬 인프라 (Docker)

ADR 0003 (pgvector) 로컬 개발 환경.

## 시작

```pwsh
cd D:\autodoxc\infra\docker
docker compose up -d
```

- Postgres 16 + pgvector + pg_trgm + pgcrypto 자동 활성화
- 초기 스키마(`src/backend/migrations/001_init.sql`) 컨테이너 첫 부팅 시 자동 실행
- 포트 5432 노출 (`autodoxc:dev-password@127.0.0.1:5432/autodoxc`)

## 백엔드 연결

`src/backend/.env`에 다음 추가:

```
DATABASE_URL=postgresql://autodoxc:dev-password@127.0.0.1:5432/autodoxc
```

설정 후 백엔드 재기동.

## 상태 점검

```pwsh
docker compose ps
docker compose logs -f postgres
```

직접 psql 접속:

```pwsh
docker compose exec postgres psql -U autodoxc -d autodoxc
```

```sql
SELECT version FROM schema_migrations;        -- 001_init 확인
\dx                                            -- vector, pg_trgm, pgcrypto 확인
\dt                                            -- 6개 테이블 확인
```

## 마이그레이션 추가

`src/backend/migrations/00N_*.sql` 형식으로 새 파일 추가 후 컨테이너 재기동 또는 수동 실행. B3에서 Alembic으로 정식 전환.

## 정리

```pwsh
docker compose down        # 컨테이너만 (데이터 보존)
docker compose down -v     # 데이터까지 (스키마 재초기화)
```
