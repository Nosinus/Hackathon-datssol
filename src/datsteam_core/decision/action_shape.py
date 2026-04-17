from __future__ import annotations

from typing import Any


def build_neutral_action_payload() -> dict[str, object]:
    """Game-agnostic no-op envelope used by generic runtime fallbacks."""
    return {"commands": []}


def extract_command_list(payload: dict[str, Any]) -> list[object] | None:
    ships = payload.get("ships")
    if isinstance(ships, list):
        return ships
    commands = payload.get("commands")
    if isinstance(commands, list):
        return commands
    return None


def is_minimally_valid_action_payload(payload: dict[str, Any]) -> bool:
    return extract_command_list(payload) is not None
