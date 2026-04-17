from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget
from games.datssol.evaluator.features import extract_features
from games.datssol.evaluator.scorer import score_scheduled_action
from games.datssol.exit_scheduler import schedule_candidates
from games.datssol.fallback import deterministic_fallback
from games.datssol.graph import Point, in_square_range, is_orthogonally_adjacent, summarize_graph
from games.datssol.legal_actions import CandidateAction, generate_candidates
from games.datssol.validator import DatsSolSemanticValidator


@dataclass(frozen=True)
class _StateSnapshot:
    main: Point | None
    main_hp: int | None
    main_progress: int | None
    main_ttf: int | None
    plantations_by_pos: dict[Point, dict[str, object]]
    occupied: set[Point]
    main_component: frozenset[Point]
    adjacent_receivers: tuple[Point, ...]
    critical_bridges: tuple[Point, ...]
    urgent_bridges: tuple[Point, ...]
    construction_by_pos: dict[Point, int]
    settlement_margin: int | None
    plantation_upgrades: dict[str, object] | None
    beaver_positions: frozenset[Point]
    beaver_threats: dict[Point, int]
    earthquake_turns_until: int | None
    sandstorm_turns: tuple[dict[str, object], ...]
    action_range: int
    map_bounds: tuple[int, int] | None
    main_under_threat: bool
    can_start_construction: bool
    preferred_construction_cap: int


@dataclass
class DatsSolBaselineStrategy:
    """Deterministic survival-first policy for DatsSol live play."""

    shortlist_size: int = 8
    predictor_horizon: int = 2
    max_parallel_constructions: int = 2
    main_hp_redline: int = 26

    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope:
        _ = budget
        if _is_idle_state(state):
            return ActionEnvelope(tick=state.tick, payload={}, reason="idle_hold")

        snapshot = _analyze_state(
            state,
            max_parallel_constructions=self.max_parallel_constructions,
            main_hp_redline=self.main_hp_redline,
        )
        if snapshot.main is None:
            return deterministic_fallback(state)

        relocate = _choose_main_relocation_payload(snapshot)
        if relocate is not None:
            return _validated_action(state, relocate, "baseline_stage2:relocate_main")

        if not snapshot.adjacent_receivers and snapshot.can_start_construction:
            receiver = _choose_adjacent_receiver_payload(state, snapshot)
            if receiver is not None:
                return _validated_action(state, receiver, "baseline_stage2:build_receiver")

        if snapshot.main_under_threat:
            repair = _choose_main_repair_payload(snapshot)
            if repair is not None:
                return _validated_action(state, repair, "baseline_stage2:repair_main")

            upgrade = _choose_survival_upgrade(snapshot)
            if upgrade is not None:
                return _validated_action(state, upgrade, f"baseline_stage2:upgrade:{upgrade['plantationUpgrade']}")

        bypass = _choose_bypass_payload(state, snapshot)
        if bypass is not None:
            return _validated_action(state, bypass, "baseline_stage2:build_bypass")

        if not snapshot.can_start_construction:
            upgrade = _choose_survival_upgrade(snapshot)
            if upgrade is not None:
                return _validated_action(state, upgrade, f"baseline_stage2:upgrade:{upgrade['plantationUpgrade']}")
            return deterministic_fallback(state)

        expansion = _choose_best_expansion_payload(state, snapshot, self.shortlist_size, self.predictor_horizon)
        if expansion is not None:
            return _validated_action(state, expansion, "baseline_stage2:expand")

        repair = _choose_main_repair_payload(snapshot)
        if repair is not None and snapshot.main_under_threat:
            return _validated_action(state, repair, "baseline_stage2:repair_main")

        upgrade = _choose_survival_upgrade(snapshot)
        if upgrade is not None:
            return _validated_action(state, upgrade, f"baseline_stage2:upgrade:{upgrade['plantationUpgrade']}")

        return deterministic_fallback(state)


def _validated_action(state: CanonicalState, payload: dict[str, object], reason: str) -> ActionEnvelope:
    action = ActionEnvelope(tick=state.tick, payload=payload, reason=reason)
    sanitized = DatsSolSemanticValidator().validate(action, state)
    if sanitized.semantic_success:
        return ActionEnvelope(tick=state.tick, payload=sanitized.payload, reason=reason)
    return deterministic_fallback(state)


def _choose_main_relocation_payload(snapshot: _StateSnapshot) -> dict[str, object] | None:
    if snapshot.main is None:
        return None
    if not _must_relocate_main(snapshot):
        return None
    if not snapshot.adjacent_receivers:
        return None

    best_target = max(
        snapshot.adjacent_receivers,
        key=lambda point: (
            _receiver_priority(point, snapshot),
            -snapshot.beaver_threats.get(point, 0),
        ),
    )
    return {"relocateMain": [list(snapshot.main), list(best_target)]}


def _choose_adjacent_receiver_payload(
    state: CanonicalState, snapshot: _StateSnapshot
) -> dict[str, object] | None:
    if snapshot.main is None:
        return None

    candidates = [
        candidate
        for candidate in generate_candidates(state)
        if candidate.path[0] == snapshot.main and is_orthogonally_adjacent(snapshot.main, candidate.path[2])
    ]
    if not candidates:
        return None

    preferred = [candidate for candidate in candidates if _is_safe_build_target(candidate.path[2], snapshot)]
    pool = preferred or candidates
    best = max(pool, key=lambda candidate: candidate.base_score + _receiver_build_bonus(candidate.path[2], snapshot))
    return {"command": [{"path": _path_to_lists(best.path)}]}


def _choose_main_repair_payload(snapshot: _StateSnapshot) -> dict[str, object] | None:
    if snapshot.main is None:
        return None

    best_source: Point | None = None
    best_score = float("-inf")
    for point, item in snapshot.plantations_by_pos.items():
        if point == snapshot.main:
            continue
        if point not in snapshot.main_component:
            continue
        if not in_square_range(point, snapshot.main, snapshot.action_range):
            continue
        hp = _safe_int(item.get("hp"), default=0)
        immunity = _safe_int(item.get("immunity_until_turn"), default=0)
        threat = snapshot.beaver_threats.get(point, 0)
        score = float(hp) + (2.0 if immunity > 0 else 0.0) - float(threat * 10)
        if score > best_score:
            best_score = score
            best_source = point

    if best_source is None:
        return None
    return {"command": [{"path": [list(best_source), list(best_source), list(snapshot.main)]}]}


def _choose_bypass_payload(state: CanonicalState, snapshot: _StateSnapshot) -> dict[str, object] | None:
    if not snapshot.urgent_bridges or not snapshot.can_start_construction:
        return None

    current_positions = list(snapshot.plantations_by_pos)
    best: CandidateAction | None = None
    best_score = float("-inf")
    for candidate in generate_candidates(state):
        target = candidate.path[2]
        if not _is_safe_build_target(target, snapshot):
            continue
        simulated = summarize_graph(plantations=current_positions + [target], main=snapshot.main)
        resolved = sum(1 for point in snapshot.urgent_bridges if point not in simulated.articulation_points)
        if resolved <= 0:
            continue
        score = candidate.base_score + (5.0 * float(resolved))
        if score > best_score:
            best_score = score
            best = candidate

    if best is None:
        return None
    return {"command": [{"path": _path_to_lists(best.path)}]}


def _choose_best_expansion_payload(
    state: CanonicalState,
    snapshot: _StateSnapshot,
    shortlist_size: int,
    predictor_horizon: int,
) -> dict[str, object] | None:
    candidates = [candidate for candidate in generate_candidates(state) if _is_safe_expansion_candidate(candidate, snapshot)]
    if not candidates:
        return None

    scheduled = schedule_candidates(candidates, limit=max(1, min(shortlist_size, 2)))
    features = extract_features(state)

    best_payload: dict[str, object] | None = None
    best_score = float("-inf")
    for item in scheduled:
        breakdown = score_scheduled_action(item, features)
        predicted = _predict_local_margin(predictor_horizon, item.exit_use_index)
        total = breakdown.total + predicted
        if total <= best_score:
            continue
        best_score = total
        best_payload = {"command": [{"path": _path_to_lists(item.candidate.path)}]}
    return best_payload


def _choose_survival_upgrade(snapshot: _StateSnapshot) -> dict[str, object] | None:
    available = _available_upgrade_names(snapshot)
    if not available:
        return None

    priority: list[str] = []
    if "repair_power" in available:
        priority.append("repair_power")
    if snapshot.beaver_threats.get(snapshot.main or (-1, -1), 0) > 0 and "beaver_damage_mitigation" in available:
        priority.append("beaver_damage_mitigation")
    if snapshot.earthquake_turns_until is not None and snapshot.earthquake_turns_until <= 1:
        if "earthquake_mitigation" in available:
            priority.append("earthquake_mitigation")
    if "signal_range" in available and not snapshot.adjacent_receivers:
        priority.append("signal_range")
    for name in (
        "repair_power",
        "signal_range",
        "beaver_damage_mitigation",
        "earthquake_mitigation",
        "max_hp",
        "decay_mitigation",
        "vision_range",
    ):
        if name in available:
            priority.append(name)

    seen: set[str] = set()
    for name in priority:
        if name in seen:
            continue
        seen.add(name)
        return {"plantationUpgrade": name}
    return None


def _analyze_state(
    state: CanonicalState,
    *,
    max_parallel_constructions: int,
    main_hp_redline: int,
) -> _StateSnapshot:
    plantations_by_pos = _plantations_by_position(state.metadata.get("plantations"))
    occupied = set(plantations_by_pos)
    construction_by_pos = _construction_progress_by_position(state.metadata.get("construction"))
    occupied.update(construction_by_pos)
    cells_by_pos = _cell_progress_by_position(state.metadata.get("cells"))

    main = _find_main(plantations_by_pos)
    main_hp = _safe_int(plantations_by_pos.get(main, {}).get("hp"), default=0) if main is not None else None
    main_progress = cells_by_pos.get(main) if main is not None else None
    main_ttf = _estimate_ttf(main_progress)
    main_component = frozenset(_points_from_nested(state.metadata.get("main_component")))
    critical_bridges = tuple(_points_from_nested(state.metadata.get("critical_bridges")))
    if main is not None and not main_component:
        graph_summary = summarize_graph(plantations=list(plantations_by_pos), main=main)
        main_component = frozenset(graph_summary.main_component)
        critical_bridges = tuple(
            point
            for point in graph_summary.articulation_points
            if point in graph_summary.main_component and point != main
        )
    beaver_positions = frozenset(_points_from_objects(state.metadata.get("beavers"), key="position"))
    beaver_threats = {
        point: sum(1 for beaver in beaver_positions if in_square_range(point, beaver, 2))
        for point in occupied
    }
    earthquake_turns_until = _forecast_turns_until(state.metadata.get("meteo_forecasts"), kind="earthquake")
    sandstorm_turns = tuple(_sandstorm_forecasts(state.metadata.get("meteo_forecasts")))
    settlement_margin = _optional_int(state.metadata.get("settlement_margin"))
    plantation_upgrades = _upgrade_metadata(state.metadata.get("plantation_upgrades"))

    urgent_bridges = tuple(
        point
        for point in critical_bridges
        if _is_bridge_urgent(
            point,
            progress=cells_by_pos.get(point),
            beaver_threat=beaver_threats.get(point, 0),
            earthquake_turns_until=earthquake_turns_until,
            sandstorms=sandstorm_turns,
        )
    )
    adjacent_receivers = tuple(
        point
        for point in plantations_by_pos
        if main is not None
        and point != main
        and point in main_component
        and is_orthogonally_adjacent(main, point)
        and _receiver_priority(point, None, plantations_by_pos, beaver_threats, sandstorm_turns) > -100.0
    )
    action_range = _safe_int(state.metadata.get("action_range"), default=1)
    map_bounds = _map_bounds(state.metadata.get("map_size"))

    main_under_threat = False
    if main is not None and main_hp is not None:
        main_under_threat = (
            main_hp <= main_hp_redline
            or beaver_threats.get(main, 0) > 0
            or (earthquake_turns_until is not None and earthquake_turns_until <= 1)
            or _is_sandstorm_threatened(main, sandstorm_turns)
        )

    can_start_construction = len(construction_by_pos) < max_parallel_constructions
    if settlement_margin is not None and settlement_margin <= 1:
        can_start_construction = False

    return _StateSnapshot(
        main=main,
        main_hp=main_hp,
        main_progress=main_progress,
        main_ttf=main_ttf,
        plantations_by_pos=plantations_by_pos,
        occupied=occupied,
        main_component=main_component,
        adjacent_receivers=adjacent_receivers,
        critical_bridges=critical_bridges,
        urgent_bridges=urgent_bridges,
        construction_by_pos=construction_by_pos,
        settlement_margin=settlement_margin,
        plantation_upgrades=plantation_upgrades,
        beaver_positions=beaver_positions,
        beaver_threats=beaver_threats,
        earthquake_turns_until=earthquake_turns_until,
        sandstorm_turns=sandstorm_turns,
        action_range=action_range,
        map_bounds=map_bounds,
        main_under_threat=main_under_threat,
        can_start_construction=can_start_construction,
        preferred_construction_cap=max_parallel_constructions,
    )


def _receiver_priority(
    point: Point,
    snapshot: _StateSnapshot | None = None,
    plantations_by_pos: dict[Point, dict[str, object]] | None = None,
    beaver_threats: dict[Point, int] | None = None,
    sandstorm_turns: tuple[dict[str, object], ...] | None = None,
) -> float:
    if snapshot is not None:
        plantations_by_pos = snapshot.plantations_by_pos
        beaver_threats = snapshot.beaver_threats
        sandstorm_turns = snapshot.sandstorm_turns
    if plantations_by_pos is None or beaver_threats is None or sandstorm_turns is None:
        return -100.0
    item = plantations_by_pos.get(point)
    if item is None:
        return -100.0
    hp = _safe_int(item.get("hp"), default=0)
    immunity = _safe_int(item.get("immunity_until_turn"), default=0)
    score = float(hp) + (4.0 if immunity > 0 else 0.0)
    score -= float(beaver_threats.get(point, 0) * 10)
    if _is_sandstorm_threatened(point, sandstorm_turns):
        score -= 5.0
    return score


def _must_relocate_main(snapshot: _StateSnapshot) -> bool:
    if snapshot.main is None:
        return False
    if snapshot.main_progress is not None and snapshot.main_progress >= 90:
        return True
    if snapshot.main_ttf is not None and snapshot.main_ttf <= 1:
        return True
    return False


def _receiver_build_bonus(target: Point, snapshot: _StateSnapshot) -> float:
    bonus = 0.0
    if _is_safe_build_target(target, snapshot):
        bonus += 2.0
    if _is_reinforced_cell(target):
        bonus += 1.0
    return bonus


def _is_safe_build_target(target: Point, snapshot: _StateSnapshot) -> bool:
    if _beaver_risk(target, snapshot) > 0:
        return False
    if _is_sandstorm_threatened(target, snapshot.sandstorm_turns):
        return False
    return True


def _is_safe_expansion_candidate(candidate: CandidateAction, snapshot: _StateSnapshot) -> bool:
    target = candidate.path[2]
    if candidate.path[0] not in snapshot.main_component:
        return False
    if snapshot.settlement_margin is not None and snapshot.settlement_margin <= 1:
        return False
    if _beaver_risk(target, snapshot) > 0:
        return False
    if _is_sandstorm_threatened(target, snapshot.sandstorm_turns):
        return False
    return True


def _predict_local_margin(predictor_horizon: int, exit_use_index: int) -> float:
    horizon_penalty = 0.08 * float(predictor_horizon)
    congestion_penalty = 0.2 * float(exit_use_index)
    return -horizon_penalty - congestion_penalty


def _available_upgrade_names(snapshot: _StateSnapshot) -> tuple[str, ...]:
    upgrades = snapshot.plantation_upgrades
    if upgrades is None:
        return tuple()
    points = upgrades.get("points")
    if not isinstance(points, int) or points <= 0:
        return tuple()
    tiers = upgrades.get("tiers")
    if not isinstance(tiers, list):
        return tuple()

    available: list[str] = []
    for item in tiers:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        current = item.get("current")
        maximum = item.get("max")
        if not isinstance(name, str):
            continue
        if not isinstance(current, int) or not isinstance(maximum, int):
            continue
        if current < maximum:
            available.append(name)
    return tuple(available)


def _is_idle_state(state: CanonicalState) -> bool:
    map_size = state.metadata.get("map_size")
    if isinstance(map_size, list) and map_size == [0, 0]:
        return True
    plantations = state.metadata.get("plantations")
    if isinstance(plantations, dict) and len(plantations) == 0:
        return True
    return False


def _plantations_by_position(raw: object) -> dict[Point, dict[str, object]]:
    out: dict[Point, dict[str, object]] = {}
    if not isinstance(raw, dict):
        return out
    for item in raw.values():
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos)):
            continue
        out[(pos[0], pos[1])] = item
    return out


def _construction_progress_by_position(raw: object) -> dict[Point, int]:
    out: dict[Point, int] = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        progress = item.get("progress")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos)):
            continue
        if not isinstance(progress, int):
            continue
        out[(pos[0], pos[1])] = progress
    return out


def _cell_progress_by_position(raw: object) -> dict[Point, int]:
    out: dict[Point, int] = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        progress = item.get("terraformationProgress")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos)):
            continue
        if not isinstance(progress, int):
            continue
        out[(pos[0], pos[1])] = progress
    return out


def _find_main(plantations_by_pos: dict[Point, dict[str, object]]) -> Point | None:
    for point, item in plantations_by_pos.items():
        if bool(item.get("is_main")):
            return point
    return None


def _points_from_nested(raw: object) -> list[Point]:
    out: list[Point] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, list) and len(item) == 2 and all(isinstance(v, int) for v in item):
            out.append((item[0], item[1]))
    return out


def _points_from_objects(raw: object, *, key: str) -> set[Point]:
    out: set[Point] = set()
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pos = item.get(key)
        if isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos):
            out.add((pos[0], pos[1]))
    return out


def _upgrade_metadata(raw: object) -> dict[str, object] | None:
    if isinstance(raw, dict):
        return raw
    return None


def _forecast_turns_until(raw: object, *, kind: str) -> int | None:
    if not isinstance(raw, list):
        return None
    values: list[int] = []
    for item in raw:
        if not isinstance(item, dict) or item.get("kind") != kind:
            continue
        turns = item.get("turnsUntil")
        if isinstance(turns, int):
            values.append(turns)
    if not values:
        return None
    return min(values)


def _sandstorm_forecasts(raw: object) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if isinstance(item, dict) and item.get("kind") == "sandstorm":
            out.append(item)
    return out


def _is_sandstorm_threatened(point: Point, sandstorms: tuple[dict[str, object], ...] | list[dict[str, object]]) -> bool:
    for item in sandstorms:
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


def _beaver_risk(point: Point, snapshot: _StateSnapshot) -> int:
    current = snapshot.beaver_threats.get(point)
    if current is not None:
        return current
    return sum(1 for beaver in snapshot.beaver_positions if in_square_range(point, beaver, 2))


def _is_bridge_urgent(
    point: Point,
    *,
    progress: int | None,
    beaver_threat: int,
    earthquake_turns_until: int | None,
    sandstorms: tuple[dict[str, object], ...],
) -> bool:
    if progress is not None and progress >= 80:
        return True
    if beaver_threat > 0:
        return True
    if earthquake_turns_until is not None and earthquake_turns_until <= 1:
        return True
    if _is_sandstorm_threatened(point, sandstorms):
        return True
    return False


def _estimate_ttf(progress: int | None) -> int | None:
    if progress is None:
        return None
    remaining = max(0, 100 - progress)
    return max(0, (remaining + 9) // 10)


def _is_reinforced_cell(point: Point) -> bool:
    return point[0] % 7 == 0 and point[1] % 7 == 0


def _path_to_lists(path: tuple[Point, Point, Point]) -> list[list[int]]:
    return [list(path[0]), list(path[1]), list(path[2])]


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _optional_int(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _map_bounds(raw: object) -> tuple[int, int] | None:
    if not isinstance(raw, list) or len(raw) != 2:
        return None
    if not isinstance(raw[0], int) or not isinstance(raw[1], int):
        return None
    if raw[0] <= 0 or raw[1] <= 0:
        return None
    return (raw[0], raw[1])
