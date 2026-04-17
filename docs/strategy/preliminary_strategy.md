# Preliminary Strategy

## Objective
Use a conservative deterministic baseline that prioritizes:
1. valid commands,
2. survivability,
3. stable runtime behavior,
4. replayability for overnight iteration.

## Current DatsBlack baseline
- Build command list for all known ships in deterministic ID order.
- Avoid risky cannon fire by default.
- Bias toward movement only when zone pressure increases.
- Always emit syntactically valid `ships` command bundle.

## Offline algorithm scaffolding now available
- safe greedy scorer,
- weighted feature scorer,
- beam-lite chooser,
- rollout/search placeholder,
- deterministic fallback.

These are intentionally game-agnostic stubs for policy A/B comparison before DatsSol contract release.

## Why this baseline
- Minimizes invalid action risk.
- Aligns with research memo: safe code-first baseline before search complexity.
- Produces consistent traces for evaluation and regression testing.

## Immediate next refinements
- wire DatsBlack legal action generation into generic candidate generator abstraction,
- add scenario buckets for “missed tactical opportunity” once a trusted domain evaluator exists,
- add per-policy holdout manifests for stability checks.
