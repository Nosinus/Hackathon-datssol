from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.offline_lab.policy import DecisionRecord
from datsteam_core.offline_lab.scenario_runner import ScenarioRunResult


@dataclass(frozen=True)
class HardCase:
    scenario_id: str
    tick: int
    policy_name: str
    reason: str
    details: dict[str, object]


@dataclass(frozen=True)
class HardCaseSelection:
    cases: list[HardCase]


def mine_hard_cases(result: ScenarioRunResult, *, min_margin: float = 0.05) -> HardCaseSelection:
    cases: list[HardCase] = []

    for policy_name, records in result.policy_records.items():
        fallback_streak = 0
        for record in records:
            _record_low_margin_cases(
                scenario_id=result.manifest.scenario_id,
                policy_name=policy_name,
                record=record,
                cases=cases,
                min_margin=min_margin,
            )

            if record.used_fallback:
                fallback_streak += 1
            else:
                fallback_streak = 0

            if fallback_streak >= 2:
                cases.append(
                    HardCase(
                        scenario_id=result.manifest.scenario_id,
                        tick=record.tick,
                        policy_name=policy_name,
                        reason="repeated_fallback_usage",
                        details={"fallback_streak": fallback_streak},
                    )
                )

    for comparison in result.comparisons:
        if comparison.disagreement_rate > 0:
            cases.append(
                HardCase(
                    scenario_id=result.manifest.scenario_id,
                    tick=-1,
                    policy_name=f"{comparison.policy_a} vs {comparison.policy_b}",
                    reason="policy_disagreement",
                    details={"disagreement_rate": comparison.disagreement_rate},
                )
            )

    return HardCaseSelection(cases=cases)


def _record_low_margin_cases(
    *,
    scenario_id: str,
    policy_name: str,
    record: DecisionRecord,
    cases: list[HardCase],
    min_margin: float,
) -> None:
    if not record.valid_action:
        cases.append(
            HardCase(
                scenario_id=scenario_id,
                tick=record.tick,
                policy_name=policy_name,
                reason="catastrophic_failure",
                details={"valid_action": False},
            )
        )

    if not record.candidate_scores:
        return

    top = record.candidate_scores[0].score
    second = record.candidate_scores[1].score if len(record.candidate_scores) > 1 else top
    margin = top - second
    if margin <= min_margin:
        cases.append(
            HardCase(
                scenario_id=scenario_id,
                tick=record.tick,
                policy_name=policy_name,
                reason="low_margin_decision",
                details={"margin": margin, "top": top, "second": second},
            )
        )
