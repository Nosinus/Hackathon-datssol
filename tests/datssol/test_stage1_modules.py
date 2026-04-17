from __future__ import annotations

from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState, TickBudget
from games.datssol.evaluator.features import extract_features
from games.datssol.exit_scheduler import schedule_candidates
from games.datssol.graph import in_square_range, summarize_graph
from games.datssol.legal_actions import generate_candidates
from games.datssol.strategy.baseline import DatsSolBaselineStrategy
from games.datssol.validator import DatsSolSemanticValidator


def _state() -> CanonicalState:
    return CanonicalState(
        tick=4,
        me=(CanonicalEntity(id="1", x=1, y=1), CanonicalEntity(id="2", x=3, y=1)),
        enemies=(),
        metadata={
            "plantations": {
                "1": {"position": [1, 1], "is_main": True, "is_isolated": False, "hp": 3},
                "2": {"position": [3, 1], "is_main": False, "is_isolated": False, "hp": 5},
            },
            "mountains": [[2, 2]],
            "signal_range": 3,
            "action_range": 1,
            "settlement_limit": 10,
            "beavers": [{"id": 5}],
            "plantation_upgrades": {"points": 1, "tiers": []},
        },
    )


def test_graph_summary_and_range() -> None:
    summary = summarize_graph(plantations=[(1, 1), (3, 1)], main=(1, 1), signal_range=3)
    assert summary.is_main_connected
    assert in_square_range((1, 1), (2, 2), 1)


def test_candidates_scheduler_and_features() -> None:
    state = _state()
    candidates = generate_candidates(state)
    assert candidates
    scheduled = schedule_candidates(candidates, limit=2)
    assert scheduled
    features = extract_features(state)
    assert features.beaver_count == 1


def test_semantic_validator_rejects_empty() -> None:
    state = _state()
    result = DatsSolSemanticValidator().validate(
        ActionEnvelope(tick=4, payload={}, reason="t"),
        state,
    )
    assert result.semantic_success is False


def test_baseline_returns_semantically_useful_payload() -> None:
    state = _state()
    action = DatsSolBaselineStrategy().choose_action(state, TickBudget(tick=4, deadline_ms=900))
    validated = DatsSolSemanticValidator().validate(action, state)
    assert validated.semantic_success


def test_graph_summary_marks_isolated_main_as_not_connected() -> None:
    summary = summarize_graph(
        plantations=[(0, 0), (10, 10), (11, 10)],
        main=(0, 0),
        signal_range=1,
    )
    assert summary.is_main_connected is False
