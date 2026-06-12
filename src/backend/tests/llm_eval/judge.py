"""LLM-as-judge — rubric 기반 정성 평가.

Dummy 모드에서는 0.85 baseline 반환 (운영상 의미 없음).
Anthropic 모드에서는 rubric을 시스템 프롬프트로 + 출력을 user message로 보내
Opus가 0.0~1.0 점수와 코멘트 반환.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.llm import LLMClient

RUBRIC_ROOT = Path(__file__).resolve().parent / "rubrics"


@dataclass
class JudgeResult:
    score: float
    comment: str
    raw: str


JUDGE_SYSTEM_TEMPLATE = """You are an expert evaluator for an LLM agent output.

Below is the rubric for this agent. Evaluate the given output strictly according to this rubric.
Respond ONLY with a JSON object in the form:
{{"score": <float 0.0 ~ 1.0>, "comment": "<one short Korean sentence>"}}

--- RUBRIC ---
{rubric}
"""


def load_rubric(agent: str) -> str:
    path = RUBRIC_ROOT / f"{agent}.md"
    if not path.exists():
        return "(rubric 없음 — score 1.0으로 간주)"
    return path.read_text(encoding="utf-8")


async def judge(
    *,
    llm: LLMClient,
    agent: str,
    output: dict,
    is_dummy: bool,
) -> JudgeResult:
    if is_dummy:
        return JudgeResult(
            score=0.85,
            comment="dummy 모드 — baseline 점수만 기록",
            raw="dummy:0.85",
        )

    rubric = load_rubric(agent)
    result = await llm.run_text(
        tier="opus",
        system=JUDGE_SYSTEM_TEMPLATE.format(rubric=rubric),
        user=json.dumps(output, ensure_ascii=False, indent=2),
        max_tokens=256,
    )
    return _parse(result.text)


def _parse(text: str) -> JudgeResult:
    # JSON 추출 시도
    match = re.search(r"\{[^{}]*\"score\"[^{}]*\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return JudgeResult(
                score=float(data.get("score", 0.0)),
                comment=str(data.get("comment", "")),
                raw=text,
            )
        except (json.JSONDecodeError, ValueError):
            pass
    return JudgeResult(score=0.0, comment="judge 응답 파싱 실패", raw=text)
