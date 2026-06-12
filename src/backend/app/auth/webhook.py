"""Clerk webhook 수신 — user/org/membership 이벤트를 자체 DB로 동기화.

데모: 페이로드 로깅만. 정식 통합 시 모델 upsert.
"""
from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    svix_signature: str | None = Header(default=None, alias="svix-signature"),
) -> dict:
    """svix-signature 검증 + 이벤트 라우팅.

    정식 구현:
        from svix.webhooks import Webhook, WebhookVerificationError
        wh = Webhook(os.environ["CLERK_WEBHOOK_SECRET"])
        body = await request.body()
        try:
            event = wh.verify(body, dict(request.headers))
        except WebhookVerificationError:
            raise HTTPException(401, "invalid signature")

        if event["type"] == "user.created":
            upsert_user(...)
        elif event["type"] == "organization.created":
            upsert_office(...)
        ...
    """
    if svix_signature is None:
        raise HTTPException(401, "missing svix-signature")
    # 데모: 검증 없이 ok 반환
    return {"status": "received", "stub": True}
