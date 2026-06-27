"""예외 → 진단 문자열 — 하부 원인 체인까지 노출.

OpenAI SDK의 APIConnectionError 등은 진짜 원인(httpx ConnectError/SSLError/타임아웃 등)을
`__cause__`로 감싼다. 폴백 사유를 사용자/로그에 노출할 때 그 체인을 펼친다.
"""
from __future__ import annotations

import re

_MAX_DEPTH = 3

# 비밀정보 마스킹 — 에러 메시지에 API 키/토큰이 섞여 노출되는 것 방지.
# (예: LocalProtocolError가 Authorization 헤더 값을 그대로 담는다.)
_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_\-]{6,}|Bearer\s+\S+|sk-proj-[A-Za-z0-9_\-]+)"
)


def redact_secrets(text: str) -> str:
    return _SECRET_RE.sub("***REDACTED***", text)


def format_exception_chain(exc: BaseException) -> str:
    parts: list[str] = []
    cur: BaseException | None = exc
    depth = 0
    while cur is not None and depth < _MAX_DEPTH:
        msg = str(cur).strip()
        parts.append(f"{type(cur).__name__}: {msg}" if msg else type(cur).__name__)
        cur = cur.__cause__ or cur.__context__
        depth += 1
    return redact_secrets(" | cause=".join(parts))
