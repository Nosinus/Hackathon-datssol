from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget


@dataclass
class DatsSolBaselineStrategy:
    """Deterministic conservative baseline for DatsSol v1."""

    prefer_boosted_cells: bool = True

    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope:
        _ = budget
        plantations = state.metadata.get("plantations")
        if not isinstance(plantations, dict) or not plantations:
            return ActionEnvelope(tick=state.tick, payload={}, reason="no_plantations_skip")

        non_isolated = [
            entity
            for entity in sorted(state.me, key=lambda e: int(e.id))
            if not _is_isolated(plantations, entity.id)
        ]
        if not non_isolated:
            return ActionEnvelope(tick=state.tick, payload={}, reason="all_isolated_skip")

        my_positions = {_pos(plantations, entity.id) for entity in state.me}
        mountains_raw = state.metadata.get("mountains")
        mountains: set[tuple[int, int]] = set()
        if isinstance(mountains_raw, list):
            for item in mountains_raw:
                if isinstance(item, list) and len(item) == 2:
                    mountains.add((int(item[0]), int(item[1])))
        settlement_limit = _safe_int(state.metadata.get("settlement_limit"), default=30)
        near_cap = len(state.me) >= settlement_limit
        map_bounds = _parse_map_bounds(state.metadata.get("map_size"))

        commands: list[dict[str, object]] = []
        for author in non_isolated:
            origin = _pos(plantations, author.id)
            target = self._pick_build_target(
                origin,
                my_positions,
                mountains,
                map_bounds=map_bounds,
            )
            if target is None:
                continue
            commands.append({"path": [list(origin), list(origin), list(target)]})
            break

        payload: dict[str, object] = {}
        if commands and not near_cap:
            payload["command"] = commands

        upgrade_name = _choose_upgrade(state)
        if upgrade_name is not None and "command" not in payload:
            payload["plantationUpgrade"] = upgrade_name

        reason = "baseline_skip"
        if "command" in payload:
            reason = "baseline_expand_safe"
        elif "plantationUpgrade" in payload:
            reason = "baseline_upgrade"
        elif near_cap:
            reason = "near_settlement_cap_skip"

        return ActionEnvelope(tick=state.tick, payload=payload, reason=reason)

    def _pick_build_target(
        self,
        origin: tuple[int, int],
        occupied: set[tuple[int, int]],
        mountains: set[tuple[int, int]],
        *,
        map_bounds: tuple[int, int] | None,
    ) -> tuple[int, int] | None:
        ox, oy = origin
        candidates: list[tuple[float, tuple[int, int]]] = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                target = (ox + dx, oy + dy)
                if map_bounds is not None and not _in_bounds(target, map_bounds):
                    continue
                if target in occupied or target in mountains:
                    continue
                score = 1.0
                if self.prefer_boosted_cells and target[0] % 7 == 0 and target[1] % 7 == 0:
                    score += 0.35
                if abs(dx) + abs(dy) == 1:
                    score += 0.1
                candidates.append((score, target))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (-item[0], item[1][0], item[1][1]))
        return candidates[0][1]


def _is_isolated(plantations: dict[str, object], entity_id: str) -> bool:
    item = plantations.get(str(entity_id))
    if not isinstance(item, dict):
        return True
    return bool(item.get("is_isolated", True))


def _pos(plantations: dict[str, object], entity_id: str) -> tuple[int, int]:
    item = plantations.get(str(entity_id))
    if not isinstance(item, dict):
        return (0, 0)
    position = item.get("position")
    if isinstance(position, list) and len(position) == 2:
        return (int(position[0]), int(position[1]))
    return (0, 0)


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    return default


def _parse_map_bounds(raw: object) -> tuple[int, int] | None:
    if not isinstance(raw, list) or len(raw) != 2:
        return None
    width, height = raw
    if not isinstance(width, int) or not isinstance(height, int):
        return None
    if width <= 0 or height <= 0:
        return None
    return (width, height)


def _in_bounds(position: tuple[int, int], bounds: tuple[int, int]) -> bool:
    x, y = position
    width, height = bounds
    return 0 <= x < width and 0 <= y < height


def _choose_upgrade(state: CanonicalState) -> str | None:
    raw = state.metadata.get("plantation_upgrades")
    if not isinstance(raw, dict):
        return None
    if _safe_int(raw.get("points"), default=0) <= 0:
        return None
    tiers = raw.get("tiers")
    if not isinstance(tiers, list):
        return None

    preferred = ["repair_power", "settlement_limit", "signal_range", "max_hp"]
    available: dict[str, tuple[int, int]] = {}
    for item in tiers:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        available[name] = (
            _safe_int(item.get("current"), default=0),
            _safe_int(item.get("max"), default=0),
        )

    for name in preferred:
        if name in available and available[name][0] < available[name][1]:
            return name
    return None
