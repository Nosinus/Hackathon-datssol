from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalEntity, CanonicalState
from games.datssol.graph import summarize_graph
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

    main_position = None
    for item in arena.plantations:
        if item.isMain and len(item.position) == 2:
            main_position = (item.position[0], item.position[1])
            break

    graph_summary = summarize_graph(
        plantations=[
            (item.position[0], item.position[1])
            for item in arena.plantations
            if len(item.position) == 2
        ],
        main=main_position,
    )
    critical_bridges = [
        point
        for point in graph_summary.articulation_points
        if point in graph_summary.main_component and point != main_position
    ]
    settlement_margin = _settlement_margin(
        settlement_limit=arena.settlementLimit,
        plantations_count=len(arena.plantations),
        construction_count=len(arena.construction),
    )

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
        "main_component": [list(point) for point in graph_summary.main_component],
        "graph_components": [list(component) for component in graph_summary.components],
        "articulation_points": [list(p) for p in graph_summary.articulation_points],
        "critical_bridges": [list(point) for point in critical_bridges],
        "settlement_margin": settlement_margin,
        "risk_summary": {
            "main_connected": graph_summary.is_main_connected,
            "component_count": len(graph_summary.components),
            "critical_bridge_count": len(critical_bridges),
            "settlement_margin": settlement_margin,
        },
        "unknown_fields": sorted((arena.model_extra or {}).keys()),
    }

    return DatsSolCanonicalState(
        state=CanonicalState(tick=arena.turnNo, me=me, enemies=enemies, metadata=metadata)
    )


def _settlement_margin(
    *,
    settlement_limit: int | None,
    plantations_count: int,
    construction_count: int,
) -> int | None:
    if settlement_limit is None:
        return None
    return settlement_limit - plantations_count - construction_count
