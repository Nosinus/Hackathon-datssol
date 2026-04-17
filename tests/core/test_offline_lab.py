from __future__ import annotations

from pathlib import Path

from datsteam_core.offline_lab import (
    BeamLiteSearch,
    CompositeOfflinePolicy,
    MinimalCandidateGenerator,
    RolloutPlaceholderSearch,
    SafeGreedyEvaluator,
    SafeHoldFallback,
    WeightedFeatureEvaluator,
    load_manifest,
    mine_hard_cases,
    run_manifest_for_policies,
)


def _make_policies() -> list[CompositeOfflinePolicy]:
    generator = MinimalCandidateGenerator()
    fallback = SafeHoldFallback()
    return [
        CompositeOfflinePolicy(
            name="safe_greedy",
            generator=generator,
            evaluator=SafeGreedyEvaluator(),
            search=BeamLiteSearch(beam_width=1),
            fallback=fallback,
        ),
        CompositeOfflinePolicy(
            name="weighted",
            generator=generator,
            evaluator=WeightedFeatureEvaluator(
                weights={"bias": 0.0, "has_ships_field": 1.0, "ship_count": 1.0, "enemy_count": 0.0}
            ),
            search=RolloutPlaceholderSearch(rollout_depth=1),
            fallback=fallback,
        ),
    ]


def test_manifest_runner_produces_policy_summaries() -> None:
    manifest_path = Path("tests/fixtures/offline_lab/scenario_manifest.json")
    manifests = load_manifest(manifest_path)
    alpha = manifests[0]

    result = run_manifest_for_policies(
        manifest=alpha, policies=_make_policies(), tick_budget_ms=250
    )

    assert result.manifest.scenario_id == "alpha"
    assert set(result.summaries) == {"safe_greedy", "weighted"}
    assert result.summaries["safe_greedy"].ticks == 3
    assert result.comparisons


def test_hard_case_mining_detects_disagreement_or_low_margin() -> None:
    manifest_path = Path("tests/fixtures/offline_lab/scenario_manifest.json")
    manifests = load_manifest(manifest_path)

    result = run_manifest_for_policies(manifest=manifests[1], policies=_make_policies())
    hard_cases = mine_hard_cases(result)

    assert hard_cases.cases
    reasons = {item.reason for item in hard_cases.cases}
    assert "low_margin_decision" in reasons or "policy_disagreement" in reasons
