"""비밀정보 마스킹 + 환경변수 공백 제거 회귀."""
from __future__ import annotations

import importlib

from app.shared.errors import format_exception_chain, redact_secrets


def test_redact_openai_key() -> None:
    msg = "Illegal header value b'Bearer  sk-proj-ABCDEF123456_xy\\n'"
    out = redact_secrets(msg)
    assert "sk-proj-ABCDEF123456" not in out
    assert "REDACTED" in out


def test_format_chain_redacts() -> None:
    try:
        raise ValueError("token sk-proj-SECRETVALUE12345 leaked")
    except ValueError as e:
        out = format_exception_chain(e)
    assert "SECRETVALUE12345" not in out
    assert "ValueError" in out


def test_config_strips_whitespace_from_keys(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "  sk-proj-withspace\n")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    import app.config as config

    config.get_settings.cache_clear()
    s = config.get_settings()
    assert s.openai_api_key == "sk-proj-withspace"  # 공백·개행 제거됨
    config.get_settings.cache_clear()  # 다른 테스트 오염 방지
    importlib.reload(config)
