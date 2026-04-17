# Datsteam Competition Agent Starter (Contract-First Baseline)

This repository is a production-oriented starter kit for Datsteam-style HTTP/JSON competitions.
It keeps a strict boundary between:
- **generic core** (`src/datsteam_core/`),
- **DatsBlack exemplar** (`src/games/datsblack/`),
- **DatsSol unknowns/placeholders** (`src/games/datssol/`).

## What is already strong

- deterministic runtime loop with typed state/action interfaces
- strict HTTP transport with retry/timeout/status/schema error classes
- replay capture and replay summary utilities
- DatsBlack typed client/models/canonicalization/validator/safe baseline
- fixture-driven offline evaluation path
- contract docs + machine-readable truth manifest
- contract consistency and OpenAPI snapshot/diff tooling

## New: offline decision-evaluation lab

The repo now includes a generic offline decision lab for replay-driven strategy iteration:

- canonical per-tick replay envelope (`replay.v2`) with action shortlist, candidate scores, fallback/validation flags, latency/budget, and parser extras
- scenario manifest runner that replays the same fixture stream against multiple policy implementations
- game-agnostic plugin interfaces for candidate generation, state evaluation, bounded search, and deterministic fallback
- offline metrics and error taxonomy buckets (invalid/fallback/timeout/disagreement/margin/unknown-field counts)
- hard-case mining utilities for catastrophic, low-margin, repeated fallback, parser anomalies, and policy disagreement scenarios
- analysis CLI for inspect/summarize/compare/worst-case export workflows

## What is intentionally unknown

DatsSol mechanics are **not** implemented because official docs may differ.
Unknowns remain isolated in placeholders and docs:
- endpoint and schema contract,
- auth header and token flow,
- timing and rate-limit behavior,
- scoring and visibility rules.

See:
- `docs/contract/implemented_vs_unknown.md`
- `docs/contract/open_questions.md`
- `docs/contract/source_priority.md`

## Canonical input locations

- `docs/input/` — canonical text-first context and active contract snapshots
- `Docs/Input/` — legacy binary archive (`.pdf/.docx`) only

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
make lint
make typecheck
make test
```

## Contract tooling

```bash
python -m scripts.check_contract_consistency
python -m scripts.openapi_diff --base docs/input/datsblack_openapi.json --candidate docs/input/datsblack_openapi.json
```

## Run paths

### Offline fixture path
```bash
make run-fixture
python -m scripts.run_runtime_fixture_loop
```

### Offline decision lab
```bash
python -m scripts.offline_decision_lab run-manifest tests/fixtures/offline_lab/scenario_manifest.json
python -m scripts.offline_decision_lab compare tests/fixtures/offline_lab/scenario_manifest.json safe_greedy weighted_feature
python -m scripts.offline_decision_lab worst-cases tests/fixtures/offline_lab/scenario_manifest.json --top-k 5
python -m scripts.offline_decision_lab export-hard-scenarios tests/fixtures/offline_lab/scenario_manifest.json logs/offline/hard_cases.json
```

### Replay summary
```bash
make summarize-replay
# or
python -m scripts.summarize_replay logs/replay
```

### Live CLI entrypoints
```bash
python -m scripts.cli fixture-run
python -m scripts.cli datsblack scan
python -m scripts.cli datsblack map
python -m scripts.cli datsblack register --mode royal
python -m scripts.cli datsblack loop --ticks 3 --dry-run
python -m scripts.cli datsblack dry-run
```

Legacy direct harness remains available:
```bash
python -m games.datsblack.live --dry-run --ticks 3
```

## Safe next step after DatsSol docs drop

Follow `docs/operations/datsol_release_hour_runbook.md`:
1. import official DatsSol contract into `docs/input/`,
2. update truth table (`.md` + `.yaml`),
3. add typed `games/datssol` models/client from official schema,
4. add fixtures + defensive tests,
5. run smoke checks before first live submit.

## Hard runtime constraints

- no external LLM calls in the live action path by default,
- deterministic fallback always available,
- never send unvalidated JSON,
- raw payload models separated from canonical internal state,
- DatsBlack is exemplar only, not DatsSol truth.
