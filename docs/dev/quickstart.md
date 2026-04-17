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

## 5. Offline decision lab workflows
```bash
python -m scripts.offline_decision_lab run-manifest tests/fixtures/offline_lab/scenario_manifest.json
python -m scripts.offline_decision_lab compare tests/fixtures/offline_lab/scenario_manifest.json safe_greedy weighted_feature
python -m scripts.offline_decision_lab worst-cases tests/fixtures/offline_lab/scenario_manifest.json --top-k 5
python -m scripts.offline_decision_lab export-hard-scenarios tests/fixtures/offline_lab/scenario_manifest.json logs/offline/hard_cases.json
```

## 6. Run fixture runtime loop + replay output
```bash
python -m scripts.run_runtime_fixture_loop
python -m scripts.summarize_replay logs/replay
python -m scripts.offline_decision_lab summarize-replay logs/replay
```

## 7. Run live-safe CLI entrypoints
```bash
python -m scripts.cli fixture-run
python -m scripts.cli datsblack scan
python -m scripts.cli datsblack map
python -m scripts.cli datsblack register --mode deathmatch
python -m scripts.cli datsblack exit --mode deathmatch
python -m scripts.cli datsblack loop --ticks 3 --dry-run
python -m scripts.cli datsblack dry-run
```

Legacy harness remains available for parity:
```bash
python -m games.datsblack.live --dry-run --ticks 3
```

## 8. Replay and map directories
- replay default: `logs/replay/`
- map cache default: `logs/maps/`
- replay summary is machine-readable JSON via `scripts/summarize_replay.py`
