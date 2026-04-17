from __future__ import annotations

import json
from pathlib import Path

from datsteam_core.runtime.loop import _extract_remaining_budget_ms
from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState, TickBudget
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


def test_arena_parsing_accepts_live_uuid_ids_and_forecast_shape() -> None:
    arena = ArenaResponse.model_validate(
        {
            "turnNo": 230,
            "nextTurnIn": 0.435,
            "size": [378, 378],
            "actionRange": 2,
            "plantations": [
                {
                    "id": "cab4e7de-6925-4491-8300-31df75f86b09",
                    "position": [126, 110],
                    "isMain": True,
                    "isIsolated": False,
                    "immunityUntilTurn": 264,
                    "hp": 50,
                }
            ],
            "enemy": [],
            "mountains": [],
            "cells": [],
            "construction": [],
            "beavers": [],
            "plantationUpgrades": None,
            "meteoForecasts": [
                {
                    "kind": "sandstorm",
                    "id": "9f29296c-1399-4090-968f-708b3733ea64",
                    "position": [210, 210],
                    "forming": False,
                    "radius": 30,
                    "nextPosition": [211, 211],
                }
            ],
        }
    )

    assert arena.plantations[0].id == "cab4e7de-6925-4491-8300-31df75f86b09"
    assert arena.meteoForecasts[0].turnsUntil is None
    assert arena.meteoForecasts[0].nextPosition == [211, 211]


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


def test_baseline_filters_targets_outside_map_bounds() -> None:
    state = CanonicalState(
        tick=1,
        me=(CanonicalEntity(id="1", x=0, y=0),),
        enemies=(),
        metadata={
            "map_size": [3, 3],
            "settlement_limit": 10,
            "plantations": {
                "1": {
                    "position": [0, 0],
                    "is_isolated": False,
                }
            },
            "mountains": [],
        },
    )

    action = DatsSolBaselineStrategy().choose_action(state, budget=TickBudget(tick=1))
    command = action.payload["command"][0]
    target = command["path"][2]

    assert target[0] >= 0
    assert target[1] >= 0
    assert target[0] < 3
    assert target[1] < 3
