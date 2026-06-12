"""오케스트레이터 — 04-orchestration.md의 메인 시퀀스 구현 (콜드스타트 stub).

#1a → #1b → #2 → #6 → editing_ready 흐름. #3, #4, #5, #7은 후속 단계에서 추가.
"""
from .main_sequence import run_main_sequence

__all__ = ["run_main_sequence"]
