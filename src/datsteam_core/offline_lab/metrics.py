from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from statistics import mean

from datsteam_core.offline_lab.policy import DecisionRecord


class ErrorBucket(str, Enum):
    ILLEGAL_INVALID = "illegal_invalid"
    TIMEOUT_BUDGET_MISS = "timeout_budget_miss"
    CATASTROPHIC_OUTCOME = "catastrophic_outcome"
    MISSED_TACTICAL_OPPORTUNITY = "missed_tactical_opportunity"
    MODEL_MISMATCH_REPLAY_INCONSISTENCY = "model_mismatch_replay_inconsistency"
    UNCERTAIN_LOW_MARGIN = "uncertain_low_margin"


@dataclass(frozen=True)
class ScenarioPolicySummary:
    policy_name: str
    scenario_id: str
    ticks: int
    invalid_action_rate: float
    fallback_rate: float
    timeout_or_budget_breach_rate: float
    parser_unknown_field_count: int
    top1_top2_margin_mean: float
    top1_top2_margin_min: float
    per_scenario_score: float
    error_buckets: dict[str, int]


@dataclass(frozen=True)
class PolicyComparison:
    policy_a: str
    policy_b: str
    disagreement_rate: float


def _margin(record: DecisionRecord) -> float:
    if len(record.candidate_scores) < 2:
        return 0.0
    return record.candidate_scores[0].score - record.candidate_scores[1].score


def summarize_policy_records(
    *,
    policy_name: str,
    scenario_id: str,
    records: list[DecisionRecord],
    parser_unknown_field_count: int = 0,
) -> ScenarioPolicySummary:
    ticks = len(records)
    if ticks == 0:
        return ScenarioPolicySummary(
            policy_name=policy_name,
            scenario_id=scenario_id,
            ticks=0,
            invalid_action_rate=0.0,
            fallback_rate=0.0,
            timeout_or_budget_breach_rate=0.0,
            parser_unknown_field_count=parser_unknown_field_count,
            top1_top2_margin_mean=0.0,
            top1_top2_margin_min=0.0,
            per_scenario_score=0.0,
            error_buckets={},
        )

    invalid = sum(1 for item in records if not item.valid_action)
    fallback = sum(1 for item in records if item.used_fallback)
    timeouts = sum(1 for item in records if item.timed_out)

    margins = [_margin(item) for item in records]
    scores = [item.candidate_scores[0].score for item in records if item.candidate_scores]

    buckets = Counter[str]()
    for item, margin in zip(records, margins, strict=False):
        if not item.valid_action:
            buckets[ErrorBucket.ILLEGAL_INVALID.value] += 1
        if item.timed_out:
            buckets[ErrorBucket.TIMEOUT_BUDGET_MISS.value] += 1
        if margin <= 0.05:
            buckets[ErrorBucket.UNCERTAIN_LOW_MARGIN.value] += 1
        if item.used_fallback:
            buckets[ErrorBucket.MODEL_MISMATCH_REPLAY_INCONSISTENCY.value] += 1

    return ScenarioPolicySummary(
        policy_name=policy_name,
        scenario_id=scenario_id,
        ticks=ticks,
        invalid_action_rate=invalid / ticks,
        fallback_rate=fallback / ticks,
        timeout_or_budget_breach_rate=timeouts / ticks,
        parser_unknown_field_count=parser_unknown_field_count,
        top1_top2_margin_mean=mean(margins),
        top1_top2_margin_min=min(margins),
        per_scenario_score=sum(scores),
        error_buckets=dict(buckets),
    )


def compare_policy_decisions(
    *,
    policy_a: str,
    policy_b: str,
    records_a: list[DecisionRecord],
    records_b: list[DecisionRecord],
) -> PolicyComparison:
    aligned = min(len(records_a), len(records_b))
    if aligned == 0:
        return PolicyComparison(policy_a=policy_a, policy_b=policy_b, disagreement_rate=0.0)

    disagreements = 0
    for left, right in zip(records_a[:aligned], records_b[:aligned], strict=False):
        if left.chosen_action.payload != right.chosen_action.payload:
            disagreements += 1

    return PolicyComparison(
        policy_a=policy_a,
        policy_b=policy_b,
        disagreement_rate=disagreements / aligned,
    )
