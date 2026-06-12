"""평가 baseline 기록·비교."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

BASELINES_PATH = Path(__file__).resolve().parent / "baselines.json"


@dataclass
class CaseBaseline:
    case_id: str
    assertion_pass: int
    assertion_fail: int
    judge_score: float


@dataclass
class Baselines:
    by_case: dict[str, CaseBaseline] = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Baselines":
        if not BASELINES_PATH.exists():
            return cls()
        raw = json.loads(BASELINES_PATH.read_text(encoding="utf-8"))
        return cls(
            by_case={
                k: CaseBaseline(**v) for k, v in raw.get("by_case", {}).items()
            }
        )

    def save(self) -> None:
        BASELINES_PATH.write_text(
            json.dumps(
                {
                    "by_case": {
                        k: {
                            "case_id": v.case_id,
                            "assertion_pass": v.assertion_pass,
                            "assertion_fail": v.assertion_fail,
                            "judge_score": v.judge_score,
                        }
                        for k, v in self.by_case.items()
                    }
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def upsert(self, key: str, baseline: CaseBaseline) -> None:
        self.by_case[key] = baseline
