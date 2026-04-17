from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget


@dataclass
class SafeBaselineStrategy:
    """Conservative deterministic baseline.

    - No cannon shots by default.
    - Keep speed stable unless ship is near zone edge.
    - Deterministic output order by ship id.
    """

    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope:
        del budget
        ships: list[dict[str, object]] = []
        zone = state.metadata.get("zone")
        zone_radius = None
        if isinstance(zone, dict):
            zone_radius = int(zone.get("radius", 0))

        for entity in sorted(state.me, key=lambda e: int(e.id)):
            cmd: dict[str, object] = {"id": int(entity.id)}
            if zone_radius is not None and zone_radius < 25:
                cmd["changeSpeed"] = 1
            ships.append(cmd)

        return ActionEnvelope(
            tick=state.tick,
            payload={"ships": ships},
            reason="safe_baseline_deterministic",
        )
