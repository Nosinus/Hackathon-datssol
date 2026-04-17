from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget


@dataclass(frozen=True)
class CandidateScore:
    action: dict[str, object]
    score: float
    features: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionRecord:
    tick: int
    chosen_action: ActionEnvelope
    candidates: tuple[dict[str, object], ...]
    candidate_scores: tuple[CandidateScore, ...]
    used_fallback: bool
    timed_out: bool
    valid_action: bool
    remaining_budget_ms: int | None = None


class CandidateGenerator(Protocol):
    def generate(self, state: CanonicalState) -> list[dict[str, object]]: ...


class StateEvaluator(Protocol):
    def score(self, state: CanonicalState, action: dict[str, object]) -> CandidateScore: ...


class BoundedSearch(Protocol):
    def choose(
        self,
        state: CanonicalState,
        budget: TickBudget,
        candidates: list[dict[str, object]],
        evaluator: StateEvaluator,
    ) -> CandidateScore: ...


class FallbackStrategy(Protocol):
    def fallback(
        self, state: CanonicalState, budget: TickBudget, reason: str
    ) -> ActionEnvelope: ...


class OfflinePolicy(Protocol):
    name: str

    def decide(self, state: CanonicalState, budget: TickBudget) -> DecisionRecord: ...
