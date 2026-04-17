# Dev Quickstart

## 1) Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
```

## 2) DatsSol env defaults
```bash
export DATASTEAM_GAME=datssol
export DATASTEAM_API_BASE_URL=https://games-test.datsteam.dev
export DATASTEAM_AUTH_HEADER=X-Auth-Token
export DATASTEAM_API_KEY=<token>
```

## 3) Required checks
```bash
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

## 4) DatsSol safest smoke path
```bash
python -m scripts.cli datssol dry-run --fixture tests/fixtures/datssol/arena_sample.json
python -m scripts.cli datssol loop --dry-run --ticks 3 --fixture tests/fixtures/datssol/arena_sample.json
python -m scripts.summarize_replay logs/replay
```

## 5) Optional live probes (token/network required)
```bash
python -m scripts.cli datssol arena
python -m scripts.cli datssol logs
```
Avoid spamming `/api/command` before validating payloads offline.
