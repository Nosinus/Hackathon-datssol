from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.replay.store import ReplayWriter
from datsteam_core.runtime.loop import RuntimeLoop
from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState, TickBudget


@dataclass
class _Provider:
    state: CanonicalState

    def poll(self) -> CanonicalState:
        return self.state


@dataclass
class _Strategy:
    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope:
        _ = budget
        return ActionEnvelope(tick=state.tick, payload={"ships": [{"id": 1}]}, reason="test")


@dataclass
class _Validator:
    def sanitize(self, action: ActionEnvelope, state: CanonicalState) -> ActionEnvelope:
        _ = state
        return action


@dataclass
class _Sink:
    last_payload: dict[str, object] | None = None

    def submit(self, action: ActionEnvelope) -> dict[str, object]:
        self.last_payload = action.payload
        return {"success": True}


def test_runtime_loop_applies_send_margin_fallback(tmp_path) -> None:
    state = CanonicalState(
        tick=1,
        me=(CanonicalEntity(id="1", x=0, y=0),),
        enemies=(),
        metadata={"tickRemainMs": 10},
    )
    sink = _Sink()
    loop = RuntimeLoop(
        state_provider=_Provider(state),
        strategy=_Strategy(),
        action_validator=_Validator(),
        action_sink=sink,
        replay_writer=ReplayWriter(tmp_path),
        send_margin_ms=50,
    )

    loop.step()
    assert sink.last_payload == {}


def test_runtime_loop_applies_send_margin_fallback_with_normalized_budget_key(tmp_path) -> None:
    state = CanonicalState(
        tick=2,
        me=(CanonicalEntity(id="1", x=0, y=0),),
        enemies=(),
        metadata={"remaining_budget_ms": 25},
    )
    sink = _Sink()
    loop = RuntimeLoop(
        state_provider=_Provider(state),
        strategy=_Strategy(),
        action_validator=_Validator(),
        action_sink=sink,
        replay_writer=ReplayWriter(tmp_path),
        send_margin_ms=50,
    )

    loop.step()
    assert sink.last_payload == {}
