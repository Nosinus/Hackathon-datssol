from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState
from games.datssol.graph import in_square_range


@dataclass(frozen=True)
class ValidationResult:
    payload: dict[str, object]
    errors: tuple[str, ...]
    semantic_success: bool


@dataclass
class DatsSolSemanticValidator:
    def validate(self, action: ActionEnvelope, state: CanonicalState) -> ValidationResult:
        payload = action.payload if isinstance(action.payload, dict) else {}
        plantations = state.metadata.get("plantations")
        if not isinstance(plantations, dict):
            return ValidationResult(
                payload={},
                errors=("missing_plantations",),
                semantic_success=False,
            )

        cleaned: list[dict[str, object]] = []
        seen_paths: set[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = set()
        errors: list[str] = []

        signal_range = _safe_int(state.metadata.get("signal_range"), default=3)
        action_range = _safe_int(state.metadata.get("action_range"), default=1)
        mountains = _mountains(state.metadata.get("mountains"))

        raw_commands = payload.get("command")
        if isinstance(raw_commands, list):
            for item in raw_commands:
                path = _extract_path(item)
                if path is None:
                    errors.append("invalid_path_shape")
                    continue
                author, exit_point, target = path
                if author not in _owned_points(plantations):
                    errors.append("unknown_author")
                    continue
                if exit_point not in _owned_points(plantations):
                    errors.append("unknown_exit")
                    continue
                if not in_square_range(author, exit_point, signal_range):
                    errors.append("exit_out_of_signal_range")
                    continue
                if not in_square_range(exit_point, target, action_range):
                    errors.append("target_out_of_action_range")
                    continue
                if author == target:
                    errors.append("self_target_rejected")
                    continue
                if target in mountains:
                    errors.append("mountain_target")
                    continue
                if path in seen_paths:
                    continue
                seen_paths.add(path)
                cleaned.append({"path": [list(author), list(exit_point), list(target)]})

        out: dict[str, object] = {}
        if cleaned:
            out["command"] = cleaned

        upgrade = payload.get("plantationUpgrade")
        if isinstance(upgrade, str) and upgrade.strip():
            out["plantationUpgrade"] = upgrade.strip()

        relocate = payload.get("relocateMain")
        if isinstance(relocate, list) and len(relocate) >= 2:
            points: list[list[int]] = []
            for item in relocate:
                if (
                    isinstance(item, list)
                    and len(item) == 2
                    and all(isinstance(v, int) for v in item)
                ):
                    points.append([item[0], item[1]])
            if len(points) >= 2:
                out["relocateMain"] = points

        semantic_success = bool(
            out.get("command")
            or out.get("plantationUpgrade")
            or out.get("relocateMain")
        )
        if not semantic_success:
            errors.append("empty_semantic_payload")
        return ValidationResult(
            payload=out,
            errors=tuple(errors),
            semantic_success=semantic_success,
        )


def _extract_path(item: object) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]] | None:
    if not isinstance(item, dict):
        return None
    path = item.get("path")
    if not isinstance(path, list) or len(path) < 3:
        return None
    out: list[tuple[int, int]] = []
    for coord in path[:3]:
        if not isinstance(coord, list) or len(coord) != 2:
            return None
        if not all(isinstance(v, int) for v in coord):
            return None
        out.append((coord[0], coord[1]))
    return (out[0], out[1], out[2])


def _owned_points(plantations: dict[str, object]) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    for item in plantations.values():
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos):
            out.add((pos[0], pos[1]))
    return out


def _mountains(raw: object) -> set[tuple[int, int]]:
    points: set[tuple[int, int]] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, list) and len(item) == 2 and all(isinstance(v, int) for v in item):
                points.add((item[0], item[1]))
    return points


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default
