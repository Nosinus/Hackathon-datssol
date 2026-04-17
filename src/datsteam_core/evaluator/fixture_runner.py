from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalState, Strategy, TickBudget


@dataclass(frozen=True)
class EvalResult:
    ticks: int
    actions: int
    invalid_actions: int


def run_offline_fixture(strategy: Strategy, states: list[CanonicalState]) -> EvalResult:
    actions = 0
    invalid = 0
    for state in states:
        action = strategy.choose_action(state, TickBudget(tick=state.tick))
        actions += 1
        if "ships" not in action.payload:
            invalid += 1
    return EvalResult(ticks=len(states), actions=actions, invalid_actions=invalid)
