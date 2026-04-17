from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState
from games.datssol.models.raw import CommandItem, CommandRequest


@dataclass
class DatsSolActionValidator:
    def sanitize(self, action: ActionEnvelope, state: CanonicalState) -> ActionEnvelope:
        raw = action.payload

        commands_payload = raw.get("command")
        parsed_items: list[dict[str, object]] = []
        if isinstance(commands_payload, list):
            for item in commands_payload:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                if not isinstance(path, list) or len(path) < 3:
                    continue
                if not all(isinstance(coord, list) and len(coord) == 2 for coord in path):
                    continue
                parsed_items.append(CommandItem.model_validate(item).model_dump(exclude_none=True))

        upgrade = raw.get("plantationUpgrade")
        normalized_upgrade = upgrade.strip() if isinstance(upgrade, str) else None
        if normalized_upgrade == "":
            normalized_upgrade = None

        relocate = raw.get("relocateMain")
        normalized_relocate: list[list[int]] | None = None
        if isinstance(relocate, list) and len(relocate) >= 2:
            if all(isinstance(coord, list) and len(coord) == 2 for coord in relocate):
                normalized_relocate = [coord for coord in relocate if isinstance(coord, list)]

        request = CommandRequest(
            command=(
                [CommandItem.model_validate(item) for item in parsed_items]
                if parsed_items
                else None
            ),
            plantationUpgrade=normalized_upgrade,
            relocateMain=normalized_relocate,
        )

        if request.has_useful_action():
            payload = request.model_dump(exclude_none=True)
        else:
            payload = {}
        return ActionEnvelope(tick=state.tick, payload=payload, reason=action.reason)
