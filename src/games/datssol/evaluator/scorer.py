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
        "main_safety": -3.0 if features.main_hp <= 26 else 0.5,
        "bridge_penalty": -0.75 * float(features.critical_bridge_count),
        "isolation_penalty": -0.5 * float(features.isolated_count),
        "beaver_pressure": -0.6 * float(features.main_beaver_threat),
        "construction_penalty": -0.4 * float(features.construction_count),
        "exit_congestion": -0.25 * float(action.exit_use_index),
        "limit_penalty": -2.5 if features.near_settlement_limit else 0.0,
        "settlement_margin_bonus": (
            0.35
            if isinstance(features.settlement_margin, int) and features.settlement_margin >= 3
            else 0.0
        ),
        "earthquake_penalty": (
            -1.2
            if features.earthquake_turns_until is not None and features.earthquake_turns_until <= 1
            else 0.0
        ),
    }
    total = sum(components.values())
    return ScoreBreakdown(total=total, components=components)
