from __future__ import annotations

import time
from dataclasses import dataclass

from datsteam_core.replay.store import ReplayWriter
from datsteam_core.types.core import (
    ActionEnvelope,
    ActionSink,
    ActionValidator,
    StateProvider,
    Strategy,
    TickBudget,
)


@dataclass
class RuntimeLoop:
    state_provider: StateProvider
    strategy: Strategy
    action_validator: ActionValidator
    action_sink: ActionSink
    replay_writer: ReplayWriter
    send_margin_ms: int = 50

    def step(self) -> dict[str, object]:
        state = self.state_provider.poll()
        remaining_budget_ms = _extract_remaining_budget_ms(state.metadata)
        budget = TickBudget(tick=state.tick, deadline_ms=remaining_budget_ms)

        proposed = self.strategy.choose_action(state, budget)
        action = self.action_validator.sanitize(proposed, state)

        fallback_due_to_margin = False
        if remaining_budget_ms is not None and remaining_budget_ms <= self.send_margin_ms:
            action = ActionEnvelope(
                tick=state.tick,
                payload={"ships": []},
                reason="send_margin_safe_hold",
            )
            fallback_due_to_margin = True

        start = time.perf_counter()
        result = self.action_sink.submit(action)
        latency_ms = int((time.perf_counter() - start) * 1000)

        self.replay_writer.write_step(
            state=state,
            action=action,
            result=result,
            request_payload=action.payload,
            latency_ms=latency_ms,
            remaining_budget_ms=remaining_budget_ms,
            fallback_flags={"send_margin_safe_hold": fallback_due_to_margin},
            validation_flags={"sanitized": proposed.payload != action.payload},
        )
        return result


def _extract_remaining_budget_ms(metadata: dict[str, object]) -> int | None:
    for key in ("tickRemainMs", "tick_remain_ms", "remaining_budget_ms"):
        value = metadata.get(key)
        if isinstance(value, int):
            return value
    return None
