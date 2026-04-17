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
    occupied = {
        tuple(v.get("position", [0, 0]))
        for v in plantations.values()
        if isinstance(v, dict)
    }
    signal_range = _safe_int(state.metadata.get("signal_range"), default=3)
    action_range = _safe_int(state.metadata.get("action_range"), default=1)
    map_bounds = _map_bounds(state.metadata.get("map_size"))

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

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                target = (src[0] + dx, src[1] + dy)
                if map_bounds is not None and not _in_bounds(target, map_bounds):
                    continue
                if target in occupied or target in mountains:
                    continue
                if not in_square_range(src, src, signal_range):
                    continue
                if not in_square_range(src, target, action_range):
                    continue
                score = 1.0 + (0.2 if abs(dx) + abs(dy) == 1 else 0.0)
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


def _to_points(raw: object) -> set[Point]:
    points: set[Point] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, list) and len(item) == 2 and all(isinstance(v, int) for v in item):
                points.add((item[0], item[1]))
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
