from __future__ import annotations

from dataclasses import dataclass

from datsteam_core.offline_lab.policy import (
    BoundedSearch,
    CandidateGenerator,
    CandidateScore,
    DecisionRecord,
    FallbackStrategy,
    OfflinePolicy,
    StateEvaluator,
)
from datsteam_core.types.core import ActionEnvelope, CanonicalState, TickBudget


@dataclass(frozen=True)
class SafeHoldFallback:
    reason: str = "safe_hold"

    def fallback(self, state: CanonicalState, budget: TickBudget, reason: str) -> ActionEnvelope:
        _ = budget
        return ActionEnvelope(
            tick=state.tick, payload={"ships": []}, reason=f"{self.reason}:{reason}"
        )


@dataclass(frozen=True)
class MinimalCandidateGenerator:
    """Game-agnostic candidate stub over generic 'ships' payload shape."""

    def generate(self, state: CanonicalState) -> list[dict[str, object]]:
        ids = [entity.id for entity in state.me]
        if not ids:
            return [{"ships": []}]
        return [
            {"ships": []},
            {"ships": [{"id": ship_id, "changeSpeed": 1} for ship_id in ids]},
            {"ships": [{"id": ship_id, "rotate": 90} for ship_id in ids]},
        ]


@dataclass(frozen=True)
class SafeGreedyEvaluator:
    """Conservative scoring that rewards non-empty legal-ish commands."""

    def score(self, state: CanonicalState, action: dict[str, object]) -> CandidateScore:
        ships = action.get("ships")
        base = 0.0
        features: dict[str, float] = {
            "has_ships_field": 1.0 if isinstance(ships, list) else 0.0,
            "ship_count": float(len(ships)) if isinstance(ships, list) else 0.0,
            "enemy_pressure": float(len(state.enemies)),
        }
        if isinstance(ships, list):
            base += 1.0
            if ships:
                base += 0.25
        return CandidateScore(action=action, score=base, features=features)


@dataclass(frozen=True)
class WeightedFeatureEvaluator:
    weights: dict[str, float]

    def score(self, state: CanonicalState, action: dict[str, object]) -> CandidateScore:
        ships = action.get("ships")
        features: dict[str, float] = {
            "bias": 1.0,
            "has_ships_field": 1.0 if isinstance(ships, list) else 0.0,
            "ship_count": float(len(ships)) if isinstance(ships, list) else 0.0,
            "enemy_count": float(len(state.enemies)),
        }
        score = 0.0
        for name, value in features.items():
            score += self.weights.get(name, 0.0) * value
        return CandidateScore(action=action, score=score, features=features)


@dataclass(frozen=True)
class BeamLiteSearch:
    beam_width: int = 2

    def choose(
        self,
        state: CanonicalState,
        budget: TickBudget,
        candidates: list[dict[str, object]],
        evaluator: StateEvaluator,
    ) -> CandidateScore:
        _ = state
        _ = budget
        scored = [evaluator.score(state, candidate) for candidate in candidates]
        ordered = sorted(scored, key=lambda item: item.score, reverse=True)
        return (
            ordered[min(max(self.beam_width, 1), len(ordered)) - 1]
            if ordered
            else CandidateScore({}, -1)
        )


@dataclass(frozen=True)
class RolloutPlaceholderSearch:
    rollout_depth: int = 1

    def choose(
        self,
        state: CanonicalState,
        budget: TickBudget,
        candidates: list[dict[str, object]],
        evaluator: StateEvaluator,
    ) -> CandidateScore:
        # Placeholder: deterministic single-step proxy until forward model exists.
        _ = budget
        _ = self.rollout_depth
        scored = [evaluator.score(state, candidate) for candidate in candidates]
        return max(scored, key=lambda item: item.score) if scored else CandidateScore({}, -1)


@dataclass(frozen=True)
class CompositeOfflinePolicy(OfflinePolicy):
    name: str
    generator: CandidateGenerator
    evaluator: StateEvaluator
    search: BoundedSearch
    fallback: FallbackStrategy

    def decide(self, state: CanonicalState, budget: TickBudget) -> DecisionRecord:
        candidates = self.generator.generate(state)
        if not candidates:
            action = self.fallback.fallback(state, budget, "no-candidates")
            return DecisionRecord(
                tick=state.tick,
                chosen_action=action,
                candidates=tuple(),
                candidate_scores=tuple(),
                used_fallback=True,
                timed_out=False,
                valid_action=isinstance(action.payload.get("ships"), list),
                remaining_budget_ms=budget.deadline_ms,
            )

        scored = [self.evaluator.score(state, candidate) for candidate in candidates]
        best = self.search.choose(state, budget, candidates, self.evaluator)

        action = ActionEnvelope(tick=state.tick, payload=best.action, reason=f"policy:{self.name}")
        valid = isinstance(action.payload.get("ships"), list)
        if not valid:
            action = self.fallback.fallback(state, budget, "invalid-action-shape")

        return DecisionRecord(
            tick=state.tick,
            chosen_action=action,
            candidates=tuple(candidates),
            candidate_scores=tuple(sorted(scored, key=lambda item: item.score, reverse=True)),
            used_fallback=not valid,
            timed_out=False,
            valid_action=valid,
            remaining_budget_ms=budget.deadline_ms,
        )
