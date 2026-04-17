from __future__ import annotations

from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState, TickBudget
from games.datsblack.strategy.baseline import SafeBaselineStrategy
from games.datsblack.strategy.legal import DatsBlackActionValidator


def _state_with_ship_meta() -> CanonicalState:
    return CanonicalState(
        tick=2,
        me=(CanonicalEntity(id="1", x=0, y=0), CanonicalEntity(id="2", x=1, y=0)),
        enemies=(),
        metadata={
            "my_ships": {
                "1": {"speed": 1, "min_speed": -1, "max_speed": 3, "max_change_speed": 2},
                "2": {"speed": 0, "min_speed": -1, "max_speed": 4, "max_change_speed": 1},
            }
        },
    )


def test_baseline_deterministic() -> None:
    state = CanonicalState(
        tick=1,
        me=(
            CanonicalEntity(id="2", x=0, y=0),
            CanonicalEntity(id="1", x=0, y=0),
        ),
        enemies=(),
        metadata={"zone": {"radius": 10}},
    )
    action = SafeBaselineStrategy().choose_action(state, TickBudget(tick=1))
    assert action.payload == {"ships": [{"id": 1, "changeSpeed": 1}, {"id": 2, "changeSpeed": 1}]}


def test_legal_validator_filters_unknown_ids() -> None:
    state = _state_with_ship_meta()
    validator = DatsBlackActionValidator()

    out = validator.sanitize(
        action=ActionEnvelope(
            tick=2, payload={"ships": [{"id": 99}, {"id": 1, "rotate": 13}]}, reason="x"
        ),
        state=state,
    )
    assert out.payload == {"ships": [{"id": 1}]}


def test_legal_validator_ignores_unparseable_commands() -> None:
    state = _state_with_ship_meta()
    validator = DatsBlackActionValidator()

    out = validator.sanitize(
        action=ActionEnvelope(
            tick=3,
            payload={
                "ships": [
                    {"id": "oops"},
                    {"id": 1, "changeSpeed": "fast"},
                    {"id": 1, "rotate": "left"},
                    {"id": 1, "rotate": 90},
                ]
            },
            reason="x",
        ),
        state=state,
    )

    assert out.payload == {"ships": [{"id": 1, "rotate": 90}]}


def test_legal_validator_dedups_and_clamps_speed() -> None:
    state = _state_with_ship_meta()
    validator = DatsBlackActionValidator()

    out = validator.sanitize(
        action=ActionEnvelope(
            tick=2,
            payload={
                "ships": [
                    {"id": 1, "changeSpeed": 10},
                    {"id": 1, "changeSpeed": -10, "rotate": 90},
                    {"id": 2, "changeSpeed": 5, "rotate": 45},
                ]
            },
            reason="x",
        ),
        state=state,
    )

    # ship 1: last command wins and delta clamped to not cross min speed (-1): 1 + (-2) => -1
    # ship 2: clamp by max_change_speed=1 and invalid rotate dropped
    assert out.payload == {
        "ships": [
            {"id": 1, "changeSpeed": -2, "rotate": 90},
            {"id": 2, "changeSpeed": 1},
        ]
    }
