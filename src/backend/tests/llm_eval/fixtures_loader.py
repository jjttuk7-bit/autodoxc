"""Fixture 로더 — `fixtures/prompts/{agent}/{case}/` 디렉토리 탐색."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FIXTURE_ROOT = Path(__file__).resolve().parents[2] / "fixtures" / "prompts"


@dataclass(frozen=True)
class FixtureCase:
    agent: str
    case_id: str
    path: Path
    input: dict[str, Any]
    expected: dict[str, Any] | None
    meta: str

    def __repr__(self) -> str:
        return f"<FixtureCase {self.agent}/{self.case_id}>"


def load_cases(agent: str) -> list[FixtureCase]:
    """주어진 에이전트의 모든 fixture case를 반환."""
    agent_dir = FIXTURE_ROOT / agent
    if not agent_dir.is_dir():
        return []
    cases: list[FixtureCase] = []
    for case_dir in sorted(agent_dir.iterdir()):
        if not case_dir.is_dir():
            continue
        input_path = case_dir / "input.json"
        if not input_path.exists():
            continue
        input_data = json.loads(input_path.read_text(encoding="utf-8"))
        expected_path = case_dir / "expected.json"
        expected_data = (
            json.loads(expected_path.read_text(encoding="utf-8"))
            if expected_path.exists()
            else None
        )
        meta_path = case_dir / "meta.md"
        meta = meta_path.read_text(encoding="utf-8") if meta_path.exists() else ""
        cases.append(
            FixtureCase(
                agent=agent,
                case_id=case_dir.name,
                path=case_dir,
                input=input_data,
                expected=expected_data,
                meta=meta,
            )
        )
    return cases
