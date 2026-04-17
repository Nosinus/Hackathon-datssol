from __future__ import annotations

from dataclasses import dataclass

from games.datssol.evaluator.features import EvalFeatures
from games.datssol.exit_scheduler import ScheduledAction


@dataclass(frozen=True)
class ScoreBreakdown:
    total: float
    components: dict[str, float]


def score_scheduled_action(action: ScheduledAction, features: EvalFeatures) -> ScoreBreakdown:
    components: dict[str, float] = {
        "base": action.adjusted_score,
        "main_safety": 2.0 if features.main_hp <= 2 else 0.5,
        "isolation_penalty": -0.5 * float(features.isolated_count),
        "limit_penalty": -2.0 if features.near_settlement_limit else 0.0,
    }
    total = sum(components.values())
    return ScoreBreakdown(total=total, components=components)
