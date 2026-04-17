from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import CanonicalState
from games.datssol.graph import Point, in_square_range


@dataclass(frozen=True)
class CandidateAction:
    path: tuple[Point, Point, Point]
    action_type: str
    base_score: float


def generate_candidates(state: CanonicalState) -> list[CandidateAction]:
    plantations = state.metadata.get("plantations")
    if not isinstance(plantations, dict):
        return []
    mountains = _to_points(state.metadata.get("mountains"))
    construction = _to_points(state.metadata.get("construction"), key="position")
    occupied = {
        tuple(v.get("position", [0, 0]))
        for v in plantations.values()
        if isinstance(v, dict)
    }
    occupied.update(construction)
    signal_range = _safe_int(state.metadata.get("signal_range"), default=3)
    action_range = _safe_int(state.metadata.get("action_range"), default=1)
    map_bounds = _map_bounds(state.metadata.get("map_size"))
    beaver_positions = _to_points(state.metadata.get("beavers"), key="position")
    meteo_forecasts = state.metadata.get("meteo_forecasts")

    out: list[CandidateAction] = []
    for key in sorted(plantations):
        item = plantations[key]
        if not isinstance(item, dict):
            continue
        if bool(item.get("is_isolated", False)):
            continue
        src = _position(item)
        if src is None:
            continue

        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            target = (src[0] + dx, src[1] + dy)
            if map_bounds is not None and not _in_bounds(target, map_bounds):
                continue
            if target in occupied or target in mountains:
                continue
            if not in_square_range(src, src, signal_range):
                continue
            if not in_square_range(src, target, action_range):
                continue
            score = 1.2 + _resource_bonus(target)
            if _is_beaver_threatened(target, beaver_positions):
                score -= 2.0
            if _is_sandstorm_threatened(target, meteo_forecasts):
                score -= 1.5
            out.append(
                CandidateAction(
                    path=(src, src, target),
                    action_type="build",
                    base_score=score,
                )
            )
    return out


def _position(item: dict[str, object]) -> Point | None:
    pos = item.get("position")
    if not isinstance(pos, list) or len(pos) != 2:
        return None
    if not isinstance(pos[0], int) or not isinstance(pos[1], int):
        return None
    return (pos[0], pos[1])


def _to_points(raw: object, *, key: str | None = None) -> set[Point]:
    points: set[Point] = set()
    if isinstance(raw, list):
        for item in raw:
            if key is None:
                if isinstance(item, list) and len(item) == 2 and all(isinstance(v, int) for v in item):
                    points.add((item[0], item[1]))
                continue
            if not isinstance(item, dict):
                continue
            pos = item.get(key)
            if isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos):
                points.add((pos[0], pos[1]))
    return points


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _map_bounds(raw: object) -> tuple[int, int] | None:
    if not isinstance(raw, list) or len(raw) != 2:
        return None
    if not isinstance(raw[0], int) or not isinstance(raw[1], int):
        return None
    if raw[0] <= 0 or raw[1] <= 0:
        return None
    return (raw[0], raw[1])


def _in_bounds(point: Point, bounds: tuple[int, int]) -> bool:
    return 0 <= point[0] < bounds[0] and 0 <= point[1] < bounds[1]


def _resource_bonus(point: Point) -> float:
    if point[0] % 7 == 0 and point[1] % 7 == 0:
        return 0.8
    return 0.0


def _is_beaver_threatened(point: Point, beavers: set[Point]) -> bool:
    return any(in_square_range(point, beaver, 2) for beaver in beavers)


def _is_sandstorm_threatened(point: Point, raw_forecasts: object) -> bool:
    if not isinstance(raw_forecasts, list):
        return False
    for item in raw_forecasts:
        if not isinstance(item, dict) or item.get("kind") != "sandstorm":
            continue
        center = item.get("position")
        radius = item.get("radius")
        if (
            isinstance(center, list)
            and len(center) == 2
            and all(isinstance(v, int) for v in center)
            and isinstance(radius, int)
            and in_square_range(point, (center[0], center[1]), radius)
        ):
            return True
        next_center = item.get("nextPosition")
        if (
            isinstance(next_center, list)
            and len(next_center) == 2
            and all(isinstance(v, int) for v in next_center)
            and isinstance(radius, int)
            and in_square_range(point, (next_center[0], next_center[1]), radius)
        ):
            return True
    return False
