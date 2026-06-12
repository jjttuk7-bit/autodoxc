"""사용자·사무소·멤버십 모델 — Clerk 메타데이터 자체 DB 복제."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """Clerk user 미러 — PII는 안 저장."""
    id: str                       # Clerk user_id
    email_domain: str | None      # PII 회피용. 전체 이메일은 Clerk만 보유
    created_at: datetime
    updated_at: datetime


class Office(BaseModel):
    """Clerk organization == 행정사 사무소."""
    id: str                       # Clerk org_id
    ko_name: str
    plan: str                     # free / pro / enterprise
    created_at: datetime


class Membership(BaseModel):
    """사용자 ↔ 사무소 N:M."""
    user_id: str
    office_id: str
    role: str                     # owner / member / viewer
    joined_at: datetime
