from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget
from games.datssol.evaluator.features import extract_features
from games.datssol.evaluator.scorer import score_scheduled_action
from games.datssol.exit_scheduler import schedule_candidates
from games.datssol.fallback import deterministic_fallback
from games.datssol.legal_actions import generate_candidates
from games.datssol.validator import DatsSolSemanticValidator


@dataclass
class DatsSolBaselineStrategy:
    """Safe deterministic Stage-1 baseline for DatsSol."""

    shortlist_size: int = 8
    predictor_horizon: int = 2

    def choose_action(self, state: CanonicalState, budget: TickBudget) -> ActionEnvelope:
        _ = budget
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
