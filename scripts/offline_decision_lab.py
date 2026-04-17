from __future__ import annotations

import argparse
import json
from dataclasses import asdict
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
from datsteam_core.replay.schema import upgrade_legacy_record
from datsteam_core.replay.summary import summarize_replay_dir


def _default_policies() -> list[CompositeOfflinePolicy]:
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
            name="weighted_feature",
            generator=generator,
            evaluator=WeightedFeatureEvaluator(
                weights={
                    "bias": 0.0,
                    "has_ships_field": 1.0,
                    "ship_count": 0.5,
                    "enemy_count": -0.1,
                }
            ),
            search=RolloutPlaceholderSearch(rollout_depth=1),
            fallback=fallback,
        ),
    ]


def cmd_inspect_replay(path: Path) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "replay.v2":
        envelope = upgrade_legacy_record(payload).to_dict()
    else:
        envelope = payload
    print(json.dumps(envelope, ensure_ascii=False, indent=2))


def cmd_summarize_replay(replay_dir: Path) -> None:
    print(json.dumps(summarize_replay_dir(replay_dir).as_dict(), ensure_ascii=False, indent=2))


def _run_manifest(path: Path, tick_budget_ms: int | None) -> list[dict[str, object]]:
    manifests = load_manifest(path)
    policies = _default_policies()
    rows: list[dict[str, object]] = []

    for manifest in manifests:
        result = run_manifest_for_policies(
            manifest=manifest,
            policies=policies,
            tick_budget_ms=tick_budget_ms,
        )
        for summary in result.summaries.values():
            rows.append(asdict(summary))
    return rows


def cmd_run_manifest(path: Path, tick_budget_ms: int | None) -> None:
    print(json.dumps(_run_manifest(path, tick_budget_ms), ensure_ascii=False, indent=2))


def cmd_compare(path: Path, policy_a: str, policy_b: str, tick_budget_ms: int | None) -> None:
    manifests = load_manifest(path)
    policies = _default_policies()
    out: list[dict[str, object]] = []

    for manifest in manifests:
        result = run_manifest_for_policies(
            manifest=manifest,
            policies=policies,
            tick_budget_ms=tick_budget_ms,
        )
        for comparison in result.comparisons:
            if {comparison.policy_a, comparison.policy_b} == {policy_a, policy_b}:
                out.append(asdict(comparison) | {"scenario_id": manifest.scenario_id})
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_worst_cases(path: Path, top_k: int, tick_budget_ms: int | None) -> None:
    manifests = load_manifest(path)
    policies = _default_policies()
    cases: list[dict[str, object]] = []

    for manifest in manifests:
        result = run_manifest_for_policies(
            manifest=manifest,
            policies=policies,
            tick_budget_ms=tick_budget_ms,
        )
        mined = mine_hard_cases(result)
        for item in mined.cases:
            cases.append(asdict(item))

    ranked = sorted(cases, key=lambda item: (item["reason"], item["tick"]))
    print(json.dumps(ranked[:top_k], ensure_ascii=False, indent=2))


def cmd_export_hard(path: Path, output: Path, top_k: int, tick_budget_ms: int | None) -> None:
    manifests = load_manifest(path)
    policies = _default_policies()
    cases: list[dict[str, object]] = []

    for manifest in manifests:
        result = run_manifest_for_policies(
            manifest=manifest,
            policies=policies,
            tick_budget_ms=tick_budget_ms,
        )
        for item in mine_hard_cases(result).cases:
            cases.append(asdict(item))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(cases[:top_k], ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output))


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline decision-evaluation lab")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_parser = sub.add_parser("inspect-replay", help="Inspect one replay envelope")
    inspect_parser.add_argument("replay_file", type=Path)

    summarize_parser = sub.add_parser("summarize-replay", help="Summarize replay directory")
    summarize_parser.add_argument("replay_dir", type=Path)

    run_parser = sub.add_parser("run-manifest", help="Run policies across a scenario manifest")
    run_parser.add_argument("manifest", type=Path)
    run_parser.add_argument("--tick-budget-ms", type=int, default=None)

    compare_parser = sub.add_parser("compare", help="Compare two policies on same manifest")
    compare_parser.add_argument("manifest", type=Path)
    compare_parser.add_argument("policy_a", type=str)
    compare_parser.add_argument("policy_b", type=str)
    compare_parser.add_argument("--tick-budget-ms", type=int, default=None)

    worst_parser = sub.add_parser("worst-cases", help="Print top-K hard cases")
    worst_parser.add_argument("manifest", type=Path)
    worst_parser.add_argument("--top-k", type=int, default=10)
    worst_parser.add_argument("--tick-budget-ms", type=int, default=None)

    export_parser = sub.add_parser("export-hard-scenarios", help="Export hard-case report")
    export_parser.add_argument("manifest", type=Path)
    export_parser.add_argument("output", type=Path)
    export_parser.add_argument("--top-k", type=int, default=20)
    export_parser.add_argument("--tick-budget-ms", type=int, default=None)

    args = parser.parse_args()

    if args.command == "inspect-replay":
        cmd_inspect_replay(args.replay_file)
    elif args.command == "summarize-replay":
        cmd_summarize_replay(args.replay_dir)
    elif args.command == "run-manifest":
        cmd_run_manifest(args.manifest, args.tick_budget_ms)
    elif args.command == "compare":
        cmd_compare(args.manifest, args.policy_a, args.policy_b, args.tick_budget_ms)
    elif args.command == "worst-cases":
        cmd_worst_cases(args.manifest, args.top_k, args.tick_budget_ms)
    elif args.command == "export-hard-scenarios":
        cmd_export_hard(args.manifest, args.output, args.top_k, args.tick_budget_ms)


if __name__ == "__main__":
    main()
