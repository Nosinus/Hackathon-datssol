from __future__ import annotations

from datsteam_core.types.core import ActionEnvelope, CanonicalState


def deterministic_fallback(state: CanonicalState) -> ActionEnvelope:
    upgrades = state.metadata.get("plantation_upgrades")
    if isinstance(upgrades, dict):
        points = upgrades.get("points")
        if isinstance(points, int) and points > 0:
            return ActionEnvelope(
                tick=state.tick,
                payload={"plantationUpgrade": "repair_power"},
                reason="fallback_upgrade_repair_power",
            )
    return ActionEnvelope(tick=state.tick, payload={}, reason="fallback_hold")
