# Runtime vs Offline Responsibilities

## Runtime (must be deterministic and resilient)
- poll state via validated transport,
- convert raw payload to canonical state,
- choose baseline action,
- sanitize/validate action,
- submit action (or skip submit safely if no useful DatsSol action exists),
- write replay telemetry (`replay.v3` envelope + run manifest metadata lineage).

## Offline decision lab (iteration loop)
- load scenario manifests and canonical tick fixtures,
- evaluate multiple policies on identical tick streams,
- compute comparable policy summaries,
- inspect replay files and summarize replay dirs,
- mine hard cases (fallback streaks, low-margin, disagreement, anomalies),
- export top-K hard scenarios to seed regression fixtures.

## Interfaces intended for extension
- `CandidateGenerator` (build legal shortlist),
- `StateEvaluator` (score candidate actions),
- `BoundedSearch` (beam-lite/search wrapper),
- `FallbackStrategy` (deterministic safe action).

## Non-goal (current baseline)
- no live LLM/model dependency in move path.

## Stage-1 runtime split

Runtime now performs deterministic graph-aware shortlist + semantic validation; deeper refinements remain offline.
