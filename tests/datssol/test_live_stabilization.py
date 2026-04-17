from __future__ import annotations

import json

from scripts.cli import _run_datssol_cycle

from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState, TickBudget
from games.datssol.models.raw import ArenaResponse, CommandRequest
from games.datssol.strategy.baseline import DatsSolBaselineStrategy
from games.datssol.timeouts import DatsSolTimeoutPolicy
from games.datssol.validator import DatsSolSemanticValidator


def _state_for_validator() -> CanonicalState:
    return CanonicalState(
        tick=10,
        me=(CanonicalEntity(id="1", x=0, y=0), CanonicalEntity(id="2", x=1, y=0)),
        enemies=(),
        metadata={
            "plantations": {
                "1": {"position": [0, 0], "is_main": True, "is_isolated": False, "hp": 3},
                "2": {"position": [1, 0], "is_main": False, "is_isolated": False, "hp": 4},
            },
            "mountains": [],
            "signal_range": 3,
            "action_range": 1,
        },
    )


def test_timeout_policy_caps_hot_path_without_overrides() -> None:
    policy = DatsSolTimeoutPolicy(base_timeout_seconds=5.0, send_margin_ms=100)
    assert 0.35 <= policy.arena_timeout(next_turn_in_seconds=0.95) <= 0.60
    assert 0.35 <= policy.command_timeout(next_turn_in_seconds=0.7) <= 0.60
    assert policy.logs_timeout() == 5.0


def test_timeout_policy_uses_optional_overrides() -> None:
    policy = DatsSolTimeoutPolicy(
        base_timeout_seconds=5.0,
        send_margin_ms=100,
        hot_timeout_seconds=0.5,
        logs_timeout_seconds=1.8,
    )
    assert policy.arena_timeout(next_turn_in_seconds=1.0) == 0.5
    assert policy.command_timeout(next_turn_in_seconds=1.0) == 0.5
    assert policy.logs_timeout() == 1.8


def test_validator_rejects_invalid_relocate_route() -> None:
    state = _state_for_validator()
    result = DatsSolSemanticValidator().validate(
        ActionEnvelope(
            tick=10,
            payload={"relocateMain": [[1, 0], [0, 0]]},
            reason="test",
        ),
        state,
    )
    assert result.semantic_success is False
    assert "invalid_relocate_main_route" in result.errors


def test_baseline_holds_on_idle_arena() -> None:
    arena = ArenaResponse.model_validate(
        {
            "turnNo": 0,
            "nextTurnIn": 1.0,
            "size": [0, 0],
            "plantations": [],
            "enemy": [],
            "mountains": [],
            "cells": [],
            "construction": [],
            "beavers": [],
            "meteoForecasts": [],
        }
    )
    from games.datssol.canonical.state import to_canonical

    state = to_canonical(arena).state
    action = DatsSolBaselineStrategy().choose_action(state, TickBudget(tick=0))
    assert action.payload == {}


def test_cycle_duplicate_submit_guard(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    class _FakeResponse:
        def model_dump(self, exclude_none: bool = True) -> dict[str, object]:
            _ = exclude_none
            return {"code": 0, "errors": []}

    class _FakeSubmit:
        response = _FakeResponse()

    class _FakeClient:
        def __init__(self) -> None:
            self.calls = 0

        def arena(self) -> ArenaResponse:
            return ArenaResponse.model_validate(
                json.loads(
                    '{"turnNo":42,"nextTurnIn":0.9,"size":[20,20],"signalRange":3,'
                    '"actionRange":1,"plantations":[{"id":1,"position":[1,1],"isMain":true,'
                    '"isIsolated":false,"hp":5},{"id":2,"position":[2,1],"isMain":false,'
                    '"isIsolated":false,"hp":5}],"enemy":[],"mountains":[],"cells":[],'
                    '"construction":[],"beavers":[],"meteoForecasts":[]}'
                )
            )

        def submit_command(
            self, payload: CommandRequest, *, next_turn_in_seconds: float | None
        ) -> _FakeSubmit:
            _ = (payload, next_turn_in_seconds)
            self.calls += 1
            return _FakeSubmit()

    client = _FakeClient()
    submitted_turns: set[int] = set()
    first = _run_datssol_cycle(client=client, do_submit=True, submitted_turns=submitted_turns)
    second = _run_datssol_cycle(client=client, do_submit=True, submitted_turns=submitted_turns)
    assert first["submit_attempted"] is True
    assert second["submit_skipped_reason"] == "duplicate_turn_guard"
    assert client.calls == 1
