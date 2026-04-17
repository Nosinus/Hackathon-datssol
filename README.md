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

### Strategy comparison scaffold
```bash
make compare-strategies
```

### Replay summary
```bash
make summarize-replay
# or
python -m scripts.summarize_replay logs/replay
```

### Live DatsBlack harness
```bash
python -m games.datsblack.live --dry-run --ticks 3
python -m games.datsblack.live --scan-only
python -m games.datsblack.live --register --mode royal --map-cache
python -m games.datsblack.live --register --mode deathmatch --ticks 5 --exit-battle
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
