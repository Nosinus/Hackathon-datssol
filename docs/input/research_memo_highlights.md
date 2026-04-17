# Research memo highlights for Codex

This is a condensed version of the longer research memo.
Treat it as the **human-approved design brief** for the overnight repo bootstrap.

## Core verdict

Build a **code-first baseline**, not an LLM-first runtime.

The live agent should remain functional without any external model call.
LLMs are for offline acceleration, repo construction, replay analysis, and tactical refinement — not the default move engine.

## Architecture split

### Live execution loop
Keep these in code:

- transport / auth
- strict validation
- canonical state conversion
- legality checks
- budget management
- deterministic fallback
- telemetry / replay logging
- strategy interface
- final action validation before sending

### Offline improvement loop
Use this for:

- replay ingestion
- batch evaluation
- failure clustering
- heuristic tuning
- simulator or forward-model work
- regression suite growth
- strategy comparisons

## Safety rules

- Never emit unvalidated JSON to the game server.
- Always keep a deterministic fallback.
- Separate raw server payloads from canonical internal state.
- Do not let a model become a single point of failure.
- Prefer robust, explainable heuristics before expensive search.

## Algorithm priority order

Use this escalation order unless the released rules strongly justify something else:

1. safe deterministic baseline
2. rule-based heuristics
3. beam search over a legal shortlist
4. domain-specific graph / geometry helpers
5. forward model / rollout search
6. learned or surrogate components later

## Evaluation priorities

Measure at least:

- validator pass rate
- invalid action rate
- timeout rate
- p50 / p95 / p99 latency
- completion / crash-free rate
- official score proxy
- p25 / tail robustness

Do not optimize only for a public leaderboard.
Preserve a hold-out mindset from the start.

## What this means for tonight

The overnight repository should emphasize:

- contract clarity,
- typed models,
- replay logs,
- fixture-driven tests,
- a safe baseline,
- future search hooks,
- clear docs on assumptions and unknowns.

It does **not** need:

- RL infrastructure,
- live multi-model orchestration,
- speculative microservices,
- risky refactors,
- production-grade scaling logic.
