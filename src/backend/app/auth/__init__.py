"""인증·세션 — ADR 0008 (Clerk 1차).

데모 단계에서는 미들웨어가 anonymous user를 반환.
정식 통합은 CLERK_SECRET_KEY 환경변수 설정 후 활성화.
"""
from .clerk_middleware import AuthContext, get_auth_context
from .models import Membership, Office, User

__all__ = [
    "AuthContext",
    "get_auth_context",
    "User",
    "Office",
    "Membership",
]
