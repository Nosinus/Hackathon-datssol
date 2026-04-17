from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget


class CandidateGenerator(Protocol):
    def generate(self, state: CanonicalState) -> list[dict[str, object]]: ...


class SafetyGate(Protocol):
    def enforce(self, state: CanonicalState, action: ActionEnvelope) -> ActionEnvelope: ...


class FastEvaluator(Protocol):
    def score(self, state: CanonicalState, action: dict[str, object]) -> float: ...


class LocalPredictor(Protocol):
    def predict(self, state: CanonicalState, horizon_ticks: int = 1) -> CanonicalState: ...


@dataclass(frozen=True)
class DecisionRecord:
    strategy_id: str
    tick: int
    action: ActionEnvelope
    action_reason: str
    candidate_count: int
    fallback_used: bool
    validator_result: dict[str, bool] = field(default_factory=dict)
    request_meta: dict[str, object] = field(default_factory=dict)


def choose_best_candidate(
    *,
    state: CanonicalState,
    budget: TickBudget,
    strategy_id: str,
    generator: CandidateGenerator,
    evaluator: FastEvaluator,
) -> DecisionRecord:
    _ = budget
    candidates = generator.generate(state)
    if not candidates:
        action = ActionEnvelope(tick=state.tick, payload={"ships": []}, reason="no-candidates")
        return DecisionRecord(
            strategy_id=strategy_id,
            tick=state.tick,
            action=action,
            action_reason=action.reason,
            candidate_count=0,
            fallback_used=True,
            validator_result={"valid": True},
        )

    best = max(candidates, key=lambda c: evaluator.score(state, c))
    action = ActionEnvelope(tick=state.tick, payload=best, reason=f"strategy:{strategy_id}")
    return DecisionRecord(
        strategy_id=strategy_id,
        tick=state.tick,
        action=action,
        action_reason=action.reason,
        candidate_count=len(candidates),
        fallback_used=False,
        validator_result={"valid": isinstance(best.get("ships"), list)},
    )
