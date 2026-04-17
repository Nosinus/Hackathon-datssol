from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalEntity, CanonicalState
from games.datssol.models.raw import ArenaResponse


@dataclass(frozen=True)
class DatsSolCanonicalState:
    state: CanonicalState


def to_canonical(arena: ArenaResponse) -> DatsSolCanonicalState:
    me = tuple(
        CanonicalEntity(id=str(item.id), x=item.position[0], y=item.position[1])
        for item in arena.plantations
    )
    enemies = tuple(
        CanonicalEntity(id=f"enemy_{item.id}", x=item.position[0], y=item.position[1])
        for item in arena.enemy
    )

    plantations_meta: dict[str, dict[str, object]] = {}
    for item in arena.plantations:
        plantations_meta[str(item.id)] = {
            "position": list(item.position),
            "is_main": item.isMain,
            "is_isolated": item.isIsolated,
            "immunity_until_turn": item.immunityUntilTurn,
            "hp": item.hp,
            "extra": item.model_extra or {},
        }

    metadata: dict[str, object] = {
        "game": "datssol",
        "turn": arena.turnNo,
        "remaining_budget_ms": int(float(arena.nextTurnIn) * 1000),
        "map_size": list(arena.size),
        "action_range": arena.actionRange,
        "signal_range": arena.signalRange,
        "vision_range": arena.visionRange,
        "settlement_limit": arena.settlementLimit,
        "plantations": plantations_meta,
        "enemy": [item.model_dump(exclude_none=True) for item in arena.enemy],
        "mountains": arena.mountains,
        "cells": [item.model_dump(exclude_none=True) for item in arena.cells],
        "construction": [item.model_dump(exclude_none=True) for item in arena.construction],
        "beavers": [item.model_dump(exclude_none=True) for item in arena.beavers],
        "plantation_upgrades": arena.plantationUpgrades.model_dump(exclude_none=True)
        if arena.plantationUpgrades
        else None,
        "meteo_forecasts": [item.model_dump(exclude_none=True) for item in arena.meteoForecasts],
        "unknown_fields": sorted((arena.model_extra or {}).keys()),
    }

    return DatsSolCanonicalState(
        state=CanonicalState(tick=arena.turnNo, me=me, enemies=enemies, metadata=metadata)
    )
