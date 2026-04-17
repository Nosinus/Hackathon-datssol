from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from datsteam_core.decision.action_shape import build_neutral_action_payload
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
            margin_fallback = ActionEnvelope(
                tick=state.tick,
                payload=build_neutral_action_payload(),
                reason="send_margin_safe_hold",
            )
            action = self.action_validator.sanitize(margin_fallback, state)
            fallback_due_to_margin = True

        start = time.perf_counter()
        result = self.action_sink.submit(action)
        latency_ms = int((time.perf_counter() - start) * 1000)
        request_meta = _extract_request_meta(self.action_sink)
        response_meta: dict[str, object] = {}
        success = result.get("success")
        if isinstance(success, bool):
            response_meta["result_success"] = success

        self.replay_writer.write_step(
            state=state,
            action=action,
            result=result,
            request_payload=action.payload,
            request_meta=request_meta,
            response_meta=response_meta,
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


def _extract_request_meta(action_sink: ActionSink) -> dict[str, Any]:
    client = getattr(action_sink, "client", None)
    transport = getattr(client, "transport", None)
    meta = getattr(transport, "last_request_meta", None)
    if meta is None:
        return {}
    return {
        "method": meta.method,
        "path": meta.path,
        "latency_ms": meta.latency_ms,
        "attempt": meta.attempt,
        "status_code": meta.status_code,
        "request_id": meta.request_id,
        "trace_id": meta.trace_id,
    }
