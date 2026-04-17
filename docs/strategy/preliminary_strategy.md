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

## Current DatsSol v1 baseline
- Expansion-first from non-isolated plantations with deterministic target ordering.
- Emits real `command[].path` payloads; never emits malformed/empty submit body.
- Opportunistically buys upgrades when points are available and no safe build is selected.
- Prioritizes safe legality and HQ/network continuity over aggressive sabotage.

## Offline algorithm scaffolding now available
- safe greedy scorer,
- weighted feature scorer,
- beam-lite chooser,
- rollout/search placeholder,
- deterministic fallback.

These remain game-agnostic stubs for policy A/B comparison around concrete DatsSol payloads.

## Why this baseline
- Minimizes invalid action risk.
- Aligns with research memo: safe code-first baseline before search complexity.
- Produces consistent traces for evaluation and regression testing.

## Immediate next refinements
- add richer DatsSol legal shortlist (build/repair/sabotage/beaver attack candidates),
- account for output-plantation overload penalty in scorer,
- add explicit HQ-relocation heuristic and meteo-aware scoring,
- keep holdout manifests for policy stability checks.

## Stage-1 baseline additions

- shortlist from legal candidates
- exit-congestion-aware scheduling
- lightweight local predictor penalty (1-3 tick proxy)
- semantic validation gate before submit
