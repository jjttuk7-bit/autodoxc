"""세션별 토큰 회계 — 04-orchestration §8 안전장치."""
from __future__ import annotations

from dataclasses import dataclass, field


class TokenBudgetExceeded(Exception):
    pass


@dataclass
class TokenBudget:
    """세션 단위 토큰 누적·상한 체크."""

    session_id: str
    limit: int
    used_input: int = 0
    used_output: int = 0
    by_agent: dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return self.used_input + self.used_output

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.total)

    def add(
        self,
        agent: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        self.used_input += input_tokens
        self.used_output += output_tokens
        self.by_agent[agent] = (
            self.by_agent.get(agent, 0) + input_tokens + output_tokens
        )
        if self.total > self.limit:
            raise TokenBudgetExceeded(
                f"세션 {self.session_id} 토큰 상한 초과: {self.total}/{self.limit}"
            )
