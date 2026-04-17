from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget
from games.datssol.evaluator.features import extract_features
from games.datssol.evaluator.scorer import score_scheduled_action
from games.datssol.exit_scheduler import schedule_candidates
from games.datssol.fallback import deterministic_fallback
from games.datssol.graph import in_square_range
from games.datssol.legal_actions import generate_candidates
from games.datssol.validator import DatsSolSemanticValidator


@dataclass
class DatsSolBaselineStrategy:
    """Safe deterministic Stage-1 baseline for DatsSol."""

    shortlist_size: int = 8
    predictor_horizon: int = 2

    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope:
        _ = budget
        if _is_idle_state(state):
            return ActionEnvelope(tick=state.tick, payload={}, reason="idle_hold")

        relocate = _safe_main_relocation_payload(state)
        if relocate is not None:
            action = ActionEnvelope(
                tick=state.tick,
                payload=relocate,
                reason="baseline_stage1:relocate_main",
            )
            sanitized = DatsSolSemanticValidator().validate(action, state)
            if sanitized.semantic_success:
                return ActionEnvelope(
                    tick=state.tick,
                    payload=sanitized.payload,
                    reason=action.reason,
                )

        candidates = generate_candidates(state)
        if not candidates:
            return deterministic_fallback(state)

        scheduled = schedule_candidates(candidates, limit=max(1, min(self.shortlist_size, 2)))
        features = extract_features(state)

        best_payload: dict[str, object] | None = None
        best_score = float("-inf")
        best_reason = "baseline_noop"
        for item in scheduled:
            breakdown = score_scheduled_action(item, features)
            predicted = self._predict_local_margin(item.exit_use_index)
            total = breakdown.total + predicted
            if total <= best_score:
                continue
            best_score = total
            best_payload = {
                "command": [
                    {
                        "path": [
                            list(item.candidate.path[0]),
                            list(item.candidate.path[1]),
                            list(item.candidate.path[2]),
                        ]
                    }
                ]
            }
            best_reason = f"baseline_stage1:{item.candidate.action_type}:score={total:.2f}"

        if best_payload is None:
            return deterministic_fallback(state)

        sanitized = DatsSolSemanticValidator().validate(
            ActionEnvelope(tick=state.tick, payload=best_payload, reason=best_reason),
            state,
        )
        if not sanitized.semantic_success:
            return deterministic_fallback(state)
        return ActionEnvelope(tick=state.tick, payload=sanitized.payload, reason=best_reason)

    def _predict_local_margin(self, exit_use_index: int) -> float:
        # Bounded local predictor proxy: penalize repeated exit use and stale concentration.
        horizon_penalty = 0.08 * float(self.predictor_horizon)
        congestion_penalty = 0.2 * float(exit_use_index)
        return -horizon_penalty - congestion_penalty


def _is_idle_state(state: CanonicalState) -> bool:
    map_size = state.metadata.get("map_size")
    if isinstance(map_size, list) and map_size == [0, 0]:
        return True
    plantations = state.metadata.get("plantations")
    if isinstance(plantations, dict) and len(plantations) == 0:
        return True
    return False


def _safe_main_relocation_payload(state: CanonicalState) -> dict[str, object] | None:
    plantations = state.metadata.get("plantations")
    if not isinstance(plantations, dict):
        return None
    signal_range = _safe_int(state.metadata.get("signal_range"), default=3)
    mountains = _to_points(state.metadata.get("mountains"))
    main: tuple[int, int] | None = None
    main_hp: int | None = None
    for value in plantations.values():
        if not isinstance(value, dict) or not bool(value.get("is_main")):
            continue
        pos = value.get("position")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos)):
            continue
        main = (pos[0], pos[1])
        hp = value.get("hp")
        main_hp = hp if isinstance(hp, int) else None
        break
    if main is None:
        return None

    must_relocate = False
    if isinstance(main_hp, int) and main_hp <= 2:
        must_relocate = True
    for cell_pos, progress in _cells(state.metadata.get("cells")):
        if cell_pos != main:
            continue
        if progress >= 90:
            must_relocate = True
            break
    if not must_relocate:
        return None

    for value in plantations.values():
        if not isinstance(value, dict):
            continue
        pos = value.get("position")
        if not (isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos)):
            continue
        dst = (pos[0], pos[1])
        if dst == main:
            continue
        if bool(value.get("is_isolated")):
            continue
        if dst in mountains:
            continue
        if in_square_range(main, dst, signal_range):
            return {"relocateMain": [list(main), list(dst)]}
    return None


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _to_points(raw: object) -> set[tuple[int, int]]:
    out: set[tuple[int, int]] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, list) and len(item) == 2 and all(isinstance(v, int) for v in item):
                out.add((item[0], item[1]))
    return out


def _cells(raw: object) -> list[tuple[tuple[int, int], int]]:
    out: list[tuple[tuple[int, int], int]] = []
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        progress = item.get("terraformationProgress")
        if not (
            isinstance(pos, list) and len(pos) == 2 and all(isinstance(v, int) for v in pos)
        ):
            continue
        if not isinstance(progress, int):
            continue
        out.append(((pos[0], pos[1]), progress))
    return out
