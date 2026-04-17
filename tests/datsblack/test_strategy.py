from __future__ import annotations

from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState, TickBudget
from games.datsblack.strategy.baseline import SafeBaselineStrategy
from games.datsblack.strategy.legal import DatsBlackActionValidator


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
    state = CanonicalState(
        tick=2,
        me=(CanonicalEntity(id="1", x=0, y=0),),
        enemies=(),
        metadata={},
    )
    validator = DatsBlackActionValidator()

    out = validator.sanitize(
        action=ActionEnvelope(
            tick=2, payload={"ships": [{"id": 99}, {"id": 1, "rotate": 13}]}, reason="x"
        ),
        state=state,
    )
    assert out.payload == {"ships": [{"id": 1}]}


def test_legal_validator_ignores_unparseable_commands() -> None:
    state = CanonicalState(
        tick=3,
        me=(CanonicalEntity(id="1", x=0, y=0),),
        enemies=(),
        metadata={},
    )
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
