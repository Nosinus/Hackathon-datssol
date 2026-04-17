from __future__ import annotations

from dataclasses import dataclass

from pydantic import ValidationError

from datsteam_core.types.core import ActionEnvelope, CanonicalState
from games.datsblack.models.raw import ShipCommand, ShipsCommands


@dataclass
class DatsBlackActionValidator:
    def sanitize(self, action: ActionEnvelope, state: CanonicalState) -> ActionEnvelope:
        ship_meta_raw = state.metadata.get("my_ships")
        ship_meta = ship_meta_raw if isinstance(ship_meta_raw, dict) else {}

        ships = action.payload.get("ships")
        if not isinstance(ships, list):
            return ActionEnvelope(tick=state.tick, payload={"ships": []}, reason="fallback_empty")

        dedup: dict[int, dict[str, object]] = {}
        for cmd in ships:
            if not isinstance(cmd, dict) or "id" not in cmd:
                continue

            try:
                sid = int(cmd["id"])
            except (TypeError, ValueError):
                continue

            if str(sid) not in ship_meta:
                continue

            try:
                model = ShipCommand.model_validate(cmd)
            except ValidationError:
                continue

            model = self._clamp_command(model, ship_meta[str(sid)])
            dedup[sid] = model.model_dump(exclude_none=True)

        payload = ShipsCommands.model_validate(
            {"ships": [dedup[k] for k in sorted(dedup.keys())]}
        ).model_dump(exclude_none=True)
        return ActionEnvelope(tick=state.tick, payload=payload, reason=action.reason)

    def _clamp_command(self, command: ShipCommand, meta_raw: object) -> ShipCommand:
        if not isinstance(meta_raw, dict):
            return command

        update: dict[str, object] = {}
        rotate = command.rotate
        if rotate is not None and rotate not in {-90, 90}:
            update["rotate"] = None

        change = command.changeSpeed
        if change is not None:
            max_change = _safe_int(meta_raw.get("max_change_speed"), 0)
            min_speed = _safe_int(meta_raw.get("min_speed"), -1)
            max_speed = _safe_int(meta_raw.get("max_speed"), 15)
            speed = _safe_int(meta_raw.get("speed"), 0)
            clamped_delta = max(-max_change, min(max_change, change))
            if speed + clamped_delta > max_speed:
                clamped_delta = max_speed - speed
            if speed + clamped_delta < min_speed:
                clamped_delta = min_speed - speed
            update["changeSpeed"] = clamped_delta

        if update:
            return command.model_copy(update=update)
        return command


def _safe_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default
