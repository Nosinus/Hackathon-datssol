from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionValidator, CanonicalState, Strategy, TickBudget


@dataclass(frozen=True)
class EvalResult:
    ticks: int
    actions: int
    invalid_actions: int
    empty_actions: int


def run_offline_fixture(
    strategy: Strategy,
    states: list[CanonicalState],
    *,
    validator: ActionValidator | None = None,
) -> EvalResult:
    actions = 0
    invalid = 0
    empty = 0
    for state in states:
        action = strategy.choose_action(state, TickBudget(tick=state.tick))
        if validator is not None:
            action = validator.sanitize(action, state)

        actions += 1
        ships = action.payload.get("ships")
        if not isinstance(ships, list):
            invalid += 1
            continue
        if not ships:
            empty += 1

    return EvalResult(
        ticks=len(states), actions=actions, invalid_actions=invalid, empty_actions=empty
    )
