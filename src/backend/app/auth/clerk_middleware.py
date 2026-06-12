"""FastAPI 의존성 — Clerk JWT 검증.

CLERK_SECRET_KEY 미설정 시: anonymous AuthContext 반환 (데모 모드).
설정 시: Authorization 헤더의 JWT를 Clerk SDK로 검증 (정식 통합 시 활성화).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from fastapi import Header


@dataclass(frozen=True)
class AuthContext:
    user_id: str | None
    office_id: str | None
    role: str | None              # owner / member / viewer / anonymous

    @property
    def is_anonymous(self) -> bool:
        return self.user_id is None


_ANONYMOUS = AuthContext(user_id=None, office_id=None, role="anonymous")


async def get_auth_context(
    authorization: str | None = Header(default=None),
) -> AuthContext:
    """B0 데모: 환경변수 없으면 anonymous. 정식 통합 시 jwt 검증 + DB 조회.

    실제 구현 예시:
        import jwt
        token = authorization.removeprefix("Bearer ").strip()
        claims = jwt.decode(token, key=..., algorithms=["RS256"], options={...})
        user_id = claims["sub"]
        office_id = claims.get("org_id")
        role = claims.get("org_role")
        return AuthContext(user_id, office_id, role)
    """
    secret = os.environ.get("CLERK_SECRET_KEY")
    if not secret or not authorization:
        return _ANONYMOUS

    # TODO: 실제 JWT 검증은 정식 통합 단계 (B3)
    # 여기서는 secret만 확인된 상태로 anonymous 반환 (보안 fallback)
    return _ANONYMOUS
