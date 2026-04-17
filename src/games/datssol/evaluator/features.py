from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalState


@dataclass(frozen=True)
class EvalFeatures:
    main_hp: int
    isolated_count: int
    near_settlement_limit: bool
    beaver_count: int
    critical_bridge_count: int
    construction_count: int
    settlement_margin: int | None
    main_beaver_threat: int
    earthquake_turns_until: int | None


def extract_features(state: CanonicalState) -> EvalFeatures:
    plantations = state.metadata.get("plantations")
    settlement_limit = state.metadata.get("settlement_limit")
    main_hp = 0
    isolated = 0
    main_position: tuple[int, int] | None = None

    if isinstance(plantations, dict):
        for item in plantations.values():
            if not isinstance(item, dict):
                continue
            if bool(item.get("is_main", False)):
                main_hp = _safe_int(item.get("hp"), default=0)
                pos = item.get("position")
                if isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos):
                    main_position = (pos[0], pos[1])
            if bool(item.get("is_isolated", False)):
                isolated += 1

    limit = _safe_int(settlement_limit, default=999)
    near_limit = len(state.me) >= max(1, limit - 1)
    beavers = state.metadata.get("beavers")
    beaver_count = len(beavers) if isinstance(beavers, list) else 0
    critical_bridges = state.metadata.get("critical_bridges")
    construction = state.metadata.get("construction")
    settlement_margin = state.metadata.get("settlement_margin")
    meteo_forecasts = state.metadata.get("meteo_forecasts")
    return EvalFeatures(
        main_hp=main_hp,
        isolated_count=isolated,
        near_settlement_limit=near_limit,
        beaver_count=beaver_count,
        critical_bridge_count=len(critical_bridges) if isinstance(critical_bridges, list) else 0,
        construction_count=len(construction) if isinstance(construction, list) else 0,
        settlement_margin=settlement_margin if isinstance(settlement_margin, int) else None,
        main_beaver_threat=_count_main_beaver_threat(main_position, beavers),
        earthquake_turns_until=_earthquake_turns_until(meteo_forecasts),
    )


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _count_main_beaver_threat(
    main_position: tuple[int, int] | None,
    beavers: object,
) -> int:
    if main_position is None or not isinstance(beavers, list):
        return 0
    total = 0
    for item in beavers:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if not (
            isinstance(pos, list)
            and len(pos) == 2
            and all(isinstance(v, int) for v in pos)
        ):
            continue
        if abs(main_position[0] - pos[0]) <= 2 and abs(main_position[1] - pos[1]) <= 2:
            total += 1
    return total


def _earthquake_turns_until(raw: object) -> int | None:
    if not isinstance(raw, list):
        return None
    values: list[int] = []
    for item in raw:
        if not isinstance(item, dict) or item.get("kind") != "earthquake":
            continue
        turns = item.get("turnsUntil")
        if isinstance(turns, int):
            values.append(turns)
    if not values:
        return None
    return min(values)
