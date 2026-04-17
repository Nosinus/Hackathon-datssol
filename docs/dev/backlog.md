# Backlog

## P0 (next)
- Wire DatsBlack legality generator into generic offline-lab candidate interface.
- Expand scenario fixture library with adversarial edge cases and parser anomaly records.
- Add p99 latency and per-endpoint histogram rollups to replay summary (p50/p95 already implemented).
- Add optional manifest bucketing by map/mode/observability tags.

## P1
- Add CI step for `scripts/check_contract_consistency.py` and OpenAPI diff gating.
- Integrate static map geometry helpers into offline tactical opportunity labeling.
- Add transport circuit-breaker style guard when repeated 5xx/timeouts occur.
- Generate/update typed models from OpenAPI snapshot script.

## P2
- Implement concrete `games/datssol` adapter after official release docs.
- Revisit auth/header abstraction once DatsSol auth contract is known.
- Add policy/compliance guardrails based on official live-round rules.
- Replace rollout placeholder with domain-validated bounded search once forward model exists.
