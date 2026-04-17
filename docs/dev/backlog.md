# Backlog

## P0 (next)
- Add long-scan decision policy (currently only hook/transport path is wired).
- Expand strategy comparison beyond scaffold baseline clone.
- Add richer map parsing once concrete map file format examples are collected.
- Add per-endpoint latency histogram export (p50/p95/p99) from live runs.

## P1
- Add CI step for `scripts/check_contract_consistency.py` and OpenAPI diff gating.
- Integrate optional static map geometry helpers into baseline safety checks.
- Add transport circuit-breaker style guard when repeated 5xx/timeouts occur.
- Generate/update typed models from OpenAPI snapshot script.

## P2
- Implement concrete `games/datssol` adapter after official release docs.
- Revisit auth/header abstraction once DatsSol auth contract is known.
- Add policy/compliance guardrails based on official live-round rules.
