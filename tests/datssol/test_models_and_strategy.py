from __future__ import annotations

import json
from pathlib import Path

from datsteam_core.runtime.loop import _extract_remaining_budget_ms
from datsteam_core.types.core import ActionEnvelope, TickBudget
from games.datssol.adapter import DatsSolActionSink
from games.datssol.canonical.state import to_canonical
from games.datssol.models.raw import ArenaResponse, CommandRequest, LogsOrError
from games.datssol.strategy.baseline import DatsSolBaselineStrategy
from games.datssol.strategy.legal import DatsSolActionValidator


def _load(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_arena_parsing_and_canonical_budget() -> None:
    arena = ArenaResponse.model_validate(_load("tests/fixtures/datssol/arena_sample.json"))
    state = to_canonical(arena).state

    assert state.tick == 91
    assert state.metadata["game"] == "datssol"
    assert state.metadata["remaining_budget_ms"] == 920


def test_logs_union_accepts_list_and_error() -> None:
    logs_ok = LogsOrError.from_api_payload(_load("tests/fixtures/datssol/logs_sample.json"))
    assert logs_ok.logs is not None
    assert len(logs_ok.logs) == 2

    logs_error = LogsOrError.from_api_payload(
        _load("tests/fixtures/datssol/logs_not_registered.json")
    )
    assert logs_error.code == 3
    assert logs_error.errors


def test_baseline_generates_useful_command_or_upgrade() -> None:
    arena = ArenaResponse.model_validate(_load("tests/fixtures/datssol/arena_sample.json"))
    state = to_canonical(arena).state

    action = DatsSolBaselineStrategy().choose_action(state, budget=TickBudget(tick=91))
    cleaned = DatsSolActionValidator().sanitize(action, state)

    assert CommandRequest.model_validate(cleaned.payload).has_useful_action() is True


def test_action_sink_skips_invalid_empty_payload() -> None:
    class _Client:
        def command(self, payload: CommandRequest):
            raise AssertionError(f"should not send command: {payload}")

    sink = DatsSolActionSink(client=_Client())
    result = sink.submit(ActionEnvelope(tick=1, payload={}, reason="skip"))
    assert "skipped" in result["errors"][0]


def test_runtime_extracts_next_turn_budget() -> None:
    assert _extract_remaining_budget_ms({"nextTurnIn": 0.81}) == 810
