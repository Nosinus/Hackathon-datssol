from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState
from games.datsblack.models.raw import ShipCommand, ShipsCommands


@dataclass
class DatsBlackActionValidator:
    def sanitize(self, action: ActionEnvelope, state: CanonicalState) -> ActionEnvelope:
        ship_ids = {int(entity.id) for entity in state.me}
        ships = action.payload.get("ships")
        if not isinstance(ships, list):
            return ActionEnvelope(tick=state.tick, payload={"ships": []}, reason="fallback_empty")
        valid: list[dict[str, object]] = []
        for cmd in ships:
            if not isinstance(cmd, dict) or "id" not in cmd:
                continue
            sid = int(cmd["id"])
            if sid not in ship_ids:
                continue
            model = ShipCommand.model_validate(cmd)
            if model.rotate is not None and model.rotate not in {-90, 90}:
                model = model.model_copy(update={"rotate": None})
            valid.append(model.model_dump(exclude_none=True))
        payload = ShipsCommands.model_validate({"ships": valid}).model_dump(exclude_none=True)
        return ActionEnvelope(tick=state.tick, payload=payload, reason=action.reason)
