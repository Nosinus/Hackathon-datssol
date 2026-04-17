# Datsteam Competition Agent Starter (Offline Baseline)

This repository provides a **production-oriented baseline** for Datsteam-style server-authoritative HTTP/JSON competitions, built to be usable immediately from offline materials.

## What this repo contains

### 1) Generic core (`src/datsteam_core/`)
- typed config loading (`env` + YAML)
- auth abstraction (header token)
- strict HTTP transport + pydantic validation
- canonical state/action interfaces
- deterministic runtime loop contract
- replay/telemetry writer (JSON per tick)
- offline evaluator scaffold for fixture-based strategy checks

### 2) DatsBlack exemplar adapter (`src/games/datsblack/`)
- raw schema models derived from bundled OpenAPI + mechanics notes
- canonical conversion from scan payload to generic canonical state
- typed API client for `map/scan/longScan/shipCommand`
- legal command sanitizer
- safe deterministic baseline strategy
- offline fixture and adapter tests

### 3) DatsSol placeholders (`src/games/datssol/`)
- explicit placeholder contract object
- unknown rules intentionally isolated behind docs and interfaces

## Repository layout

```text
src/
  datsteam_core/
    auth/
    config/
    evaluator/
    replay/
    runtime/
    transport/
    types/
  games/
    datsblack/
      api/
      canonical/
      models/
      strategy/
      fixtures/
    datssol/
docs/
  input/
  contract/
  strategy/
  dev/
tests/
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env  # edit token/base URL as needed
make test
make run-fixture
```

See `docs/dev/quickstart.md` for full details.

## Design constraints enforced in code
- no external LLM calls in the runtime path by default
- deterministic fallback-friendly strategy path
- raw payload models separated from canonical internal state
- validated JSON in/out around transport boundary
- fixture-first offline testability (no live server dependency)

## Important caveat
This repository does **not** claim DatsSol mechanics are known. DatsBlack is used only as a concrete adapter proving architecture and coding standards under a known contract.

## Input source path note
Original offline materials are kept in `Docs/Input/`; only text-first files are mirrored into `docs/input/` to keep PR diffs compatible with Codex Cloud (no binary attachments in diff).
