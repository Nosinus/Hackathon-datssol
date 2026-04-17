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
from datsteam_core.offline_lab.policy import CandidateScore
from datsteam_core.types.core import CanonicalEntity, CanonicalState, TickBudget


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
                weights={
                    "bias": 0.0,
                    "has_command_list": 1.0,
                    "command_count": 1.0,
                    "enemy_count": 0.0,
                }
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


def test_beam_lite_search_returns_best_scoring_candidate_even_with_wider_beam() -> None:
    state = CanonicalState(
        tick=1,
        me=(CanonicalEntity(id="m1", x=0, y=0),),
        enemies=(),
        metadata={},
    )
    candidates = [
        {"ships": [{"id": "m1", "changeSpeed": 1}]},
        {"ships": [{"id": "m1", "rotate": 90}]},
    ]
    evaluator = WeightedFeatureEvaluator(
        weights={"bias": 0.0, "has_command_list": 0.0, "command_count": 1.0, "enemy_count": 0.0}
    )
    # Make candidate[0] strictly better by adding one more command object.
    candidates[0] = {
        "ships": [{"id": "m1", "changeSpeed": 1}, {"id": "m1", "rotate": 90}],
    }

    chosen = BeamLiteSearch(beam_width=2).choose(
        state=state,
        budget=TickBudget(tick=1),
        candidates=candidates,
        evaluator=evaluator,
    )

    assert chosen.action == candidates[0]


class _InvalidSearch:
    def choose(  # noqa: PLR0913
        self,
        state: CanonicalState,
        budget: TickBudget,
        candidates: list[dict[str, object]],
        evaluator: SafeGreedyEvaluator,
    ) -> CandidateScore:
        _ = state
        _ = budget
        _ = candidates
        _ = evaluator
        return CandidateScore(action={"bad": "shape"}, score=999.0)


def test_policy_recomputes_validity_after_fallback_replacement() -> None:
    policy = CompositeOfflinePolicy(
        name="fallback-validity",
        generator=MinimalCandidateGenerator(),
        evaluator=SafeGreedyEvaluator(),
        search=_InvalidSearch(),
        fallback=SafeHoldFallback(),
    )
    state = CanonicalState(
        tick=2,
        me=(CanonicalEntity(id="m1", x=1, y=1),),
        enemies=(),
        metadata={},
    )

    decision = policy.decide(state, TickBudget(tick=state.tick))

    assert decision.used_fallback is True
    assert decision.valid_action is False
    assert decision.chosen_action.payload == {}
