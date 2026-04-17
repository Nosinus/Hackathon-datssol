from __future__ import annotations

from typing import Any


def build_neutral_action_payload() -> dict[str, object]:
    """Game-agnostic no-op envelope used by generic runtime fallbacks."""
    return {}


def extract_command_list(payload: dict[str, Any]) -> list[object] | None:
    command = payload.get("command")
    if isinstance(command, list):
        return command
    ships = payload.get("ships")
    if isinstance(ships, list):
        return ships
    commands = payload.get("commands")
    if isinstance(commands, list):
        return commands
    return None


def is_minimally_valid_action_payload(payload: dict[str, Any]) -> bool:
    commands = extract_command_list(payload)
    if isinstance(commands, list):
        if "command" in payload:
            return len(commands) > 0
        return True
    upgrade = payload.get("plantationUpgrade")
    if isinstance(upgrade, str) and upgrade.strip() != "":
        return True
    relocate = payload.get("relocateMain")
    if isinstance(relocate, list) and len(relocate) >= 2:
        return True
    return False
