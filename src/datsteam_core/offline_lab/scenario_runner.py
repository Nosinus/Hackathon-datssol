from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datsteam_core.offline_lab.metrics import (
    PolicyComparison,
    ScenarioPolicySummary,
    compare_policy_decisions,
    summarize_policy_records,
)
from datsteam_core.offline_lab.policy import DecisionRecord, OfflinePolicy
from datsteam_core.types.core import CanonicalEntity, CanonicalState, TickBudget


@dataclass(frozen=True)
class ScenarioManifest:
    scenario_id: str
    description: str
    source: str
    ticks_file: Path

    @staticmethod
    def from_dict(payload: dict[str, Any], *, base_dir: Path) -> ScenarioManifest:
        return ScenarioManifest(
            scenario_id=str(payload["scenario_id"]),
            description=str(payload.get("description", "")),
            source=str(payload.get("source", "fixture")),
            ticks_file=(base_dir / str(payload["ticks_file"]))
            if not Path(str(payload["ticks_file"])).is_absolute()
            else Path(str(payload["ticks_file"])),
        )


@dataclass(frozen=True)
class ScenarioRunResult:
    manifest: ScenarioManifest
    summaries: dict[str, ScenarioPolicySummary]
    policy_records: dict[str, list[DecisionRecord]]
    comparisons: list[PolicyComparison]


def load_manifest(path: Path) -> list[ScenarioManifest]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Scenario manifest must be a JSON list")
    base_dir = path.parent
    return [
        ScenarioManifest.from_dict(item, base_dir=base_dir)
        for item in payload
        if isinstance(item, dict)
    ]


def _parse_state(item: dict[str, Any]) -> CanonicalState:
    me = tuple(
        CanonicalEntity(
            id=str(entity["id"]),
            x=int(entity["x"]),
            y=int(entity["y"]),
        )
        for entity in item.get("me", [])
        if isinstance(entity, dict)
    )
    enemies = tuple(
        CanonicalEntity(
            id=str(entity["id"]),
            x=int(entity["x"]),
            y=int(entity["y"]),
        )
        for entity in item.get("enemies", [])
        if isinstance(entity, dict)
    )
    metadata = item.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    return CanonicalState(
        tick=int(item["tick"]),
        me=me,
        enemies=enemies,
        metadata=metadata,
    )


def load_scenario_ticks(path: Path) -> list[CanonicalState]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Scenario ticks file must contain a JSON list")
    return [_parse_state(item) for item in payload if isinstance(item, dict)]


def run_manifest_for_policies(
    *,
    manifest: ScenarioManifest,
    policies: list[OfflinePolicy],
    tick_budget_ms: int | None = None,
    parser_unknown_field_count: int = 0,
) -> ScenarioRunResult:
    states = load_scenario_ticks(manifest.ticks_file)

    policy_records: dict[str, list[DecisionRecord]] = {}
    summaries: dict[str, ScenarioPolicySummary] = {}

    for policy in policies:
        records: list[DecisionRecord] = []
        for state in states:
            records.append(
                policy.decide(state, TickBudget(tick=state.tick, deadline_ms=tick_budget_ms))
            )
        policy_records[policy.name] = records
        summaries[policy.name] = summarize_policy_records(
            policy_name=policy.name,
            scenario_id=manifest.scenario_id,
            records=records,
            parser_unknown_field_count=parser_unknown_field_count,
        )

    comparisons: list[PolicyComparison] = []
    for idx, left in enumerate(policies):
        for right in policies[idx + 1 :]:
            comparisons.append(
                compare_policy_decisions(
                    policy_a=left.name,
                    policy_b=right.name,
                    records_a=policy_records[left.name],
                    records_b=policy_records[right.name],
                )
            )

    return ScenarioRunResult(
        manifest=manifest,
        summaries=summaries,
        policy_records=policy_records,
        comparisons=comparisons,
    )
