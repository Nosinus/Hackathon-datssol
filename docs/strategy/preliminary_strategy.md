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

## Why this baseline
- Minimizes invalid action risk.
- Aligns with research memo: safe code-first baseline before search complexity.
- Produces consistent traces for evaluation and regression testing.

## Immediate next refinements
- zone-aware pathing heuristics,
- friend/foe collision-risk map,
- opportunistic low-risk shooting policy,
- offline A/B tests via fixture runner.
