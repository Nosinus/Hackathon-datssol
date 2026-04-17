# Dev Quickstart

## 1. Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 2. Configure
```bash
cp .env.example .env
# optional: edit config.sample.yaml and pass --config
```

## 3. Run checks
```bash
make lint
make typecheck
make test
python -m scripts.check_contract_consistency
```

## 4. Run offline multi-tick fixture evaluation
```bash
make run-fixture
python -m scripts.compare_datsblack_strategies
```

## 5. Run fixture runtime loop + replay output
```bash
python -m scripts.run_runtime_fixture_loop
python -m scripts.summarize_replay logs/replay
```

## 6. Run live DatsBlack harness
Dry-run (no submit):
```bash
python -m games.datsblack.live --dry-run --ticks 3
```

Scan-only:
```bash
python -m games.datsblack.live --scan-only
```

Register + map cache + live submit:
```bash
python -m games.datsblack.live --register --mode royal --map-cache --ticks 3
```

Deathmatch lifecycle:
```bash
python -m games.datsblack.live --register --mode deathmatch --ticks 3 --exit-battle
```

## 7. Replay and map directories
- replay default: `logs/replay/`
- map cache default: `logs/maps/`
- replay summary is machine-readable JSON via `scripts/summarize_replay.py`
