# Dev Quickstart

## 1) Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
```
`load_from_env()` автоматически подхватит `.env`; вручную экспортированные переменные имеют приоритет.

## 2) Baseline checks
```bash
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

## 3) Fixture runtime + replay summary
```bash
python -m scripts.run_runtime_fixture_loop
python -m scripts.summarize_replay logs/replay
```

## 4) Offline decision lab
```bash
python -m scripts.offline_decision_lab run-manifest tests/fixtures/offline_lab/scenario_manifest.json
python -m scripts.offline_decision_lab compare tests/fixtures/offline_lab/scenario_manifest.json safe_greedy weighted_feature
python -m scripts.offline_decision_lab worst-cases tests/fixtures/offline_lab/scenario_manifest.json --top-k 5
```

## 5) Run manifests + telemetry lineage
```bash
python -m scripts.cli ops create-manifest --output ops/manifests/run_a.json --policy-id safe_baseline --mode training --environment local
python -m scripts.cli datsblack loop --dry-run --ticks 3 --manifest ops/manifests/run_a.json
```

## 6) SQLite ingestion + post-run analytics
```bash
python -m scripts.replay_analytics ingest --replay-dir logs/replay --manifest-dir ops/manifests
python -m scripts.replay_analytics summarize-run <run_id>
python -m scripts.replay_analytics compare-runs <run_a> <run_b>
python -m scripts.replay_analytics export-anomalies <run_id> logs/offline/anomalies.json
```

## 7) Deployment smoke
```bash
docker build -t datsteam-agent:predoc .
docker run --rm -v "$(pwd)/logs:/app/logs" datsteam-agent:predoc fixture-run
# or
docker compose up --build datsteam-agent
```

## 8) DatsSol import prep helper
```bash
python -m scripts.prepare_datssol_import --tag 20260417T180000Z
```
См. пошаговый чеклист: `docs/dev/release_hour_import.md`.
