# Datsteam Competition Agent Starter (Offline Baseline)

This repository provides a **production-oriented pre-release harness** for Datsteam-style HTTP/JSON competitions and keeps a strict split between:
- generic core,
- concrete DatsBlack exemplar,
- DatsSol placeholders (unknown schema/mechanics remain isolated).

## What this repo contains

### 1) Generic core (`src/datsteam_core/`)
- typed config loading (`env` + YAML)
- auth abstraction (header token)
- strict HTTP transport with retries/backoff and timeout/status/schema error classes
- canonical state/action interfaces and runtime loop
- replay writer + replay summary utility
- fixture evaluator scaffold with validator integration

### 2) DatsBlack exemplar adapter (`src/games/datsblack/`)
- raw schema models from bundled OpenAPI
- typed API client for scan/command/map/registration/exit endpoints
- live entrypoint: `python -m games.datsblack.live`
- map fetch/cache helper via `mapUrl`
- canonical conversion with richer tactical metadata for ships
- stricter command sanitizer (dedupe, clamp, rotate checks)
- safe deterministic baseline strategy

### 3) DatsSol placeholders (`src/games/datssol/`)
- explicit placeholders/interfaces only
- no guessed DatsSol mechanics or schema

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

## Run paths

### Offline fixture path (multi-tick)
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

Config source:
- default: environment variables
- optional: `--config config.sample.yaml`

## Design constraints enforced in code
- no external LLM calls in the runtime path
- deterministic baseline and validator before submit
- no unvalidated JSON emitted
- raw models separated from canonical state
- fixture-first local validation and replay analysis

## Important caveat
This repository does **not** claim DatsSol mechanics are known. DatsBlack remains a concrete exemplar only; DatsSol implementation must wait for official docs.
