# Datsteam Competition Agent Starter (predoc release-ready contour)

Репозиторий держит строгую границу:
- **generic core**: `src/datsteam_core/`
- **DatsBlack exemplar**: `src/games/datsblack/`
- **DatsSol placeholders (unknowns only)**: `src/games/datssol/`

## Что уже готово
- deterministic runtime + action validation + fallback,
- replay envelope `replay.v3` с run metadata (`run_id/session_id/policy_id/config_hash/git_sha/mode/environment`),
- offline decision lab и hard-case mining,
- SQLite ingest + post-run analytics,
- benchmark CLI для latency contour,
- deployment contour: `Dockerfile`, `.dockerignore`, `compose.yaml`,
- import-prep для релиза DatsSol без угадывания механики.

## Быстрый старт
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
make lint
make typecheck
make test
```

## Deployment contour
```bash
docker build -t datsteam-agent:predoc .
docker run --rm -v "$(pwd)/logs:/app/logs" datsteam-agent:predoc fixture-run
# или
make container-smoke
```
Подробно: `docs/operations/deployment.md`.

## Offline lab и replay
```bash
python -m scripts.run_runtime_fixture_loop
python -m scripts.summarize_replay logs/replay
python -m scripts.offline_decision_lab run-manifest tests/fixtures/offline_lab/scenario_manifest.json
```

## Training-round run manifest + live telemetry
```bash
python -m scripts.cli ops create-manifest --output ops/manifests/run_a.json --policy-id safe_baseline --mode training --environment local
python -m scripts.cli datsblack loop --dry-run --ticks 5 --manifest ops/manifests/run_a.json
```
Теперь у каждого replay-тика есть ссылочная мета-информация о коде и конфиге этого запуска.

## Post-run analytics (SQLite contour)
```bash
python -m scripts.replay_analytics ingest --replay-dir logs/replay --manifest-dir ops/manifests
python -m scripts.replay_analytics summarize-run <run_id>
python -m scripts.replay_analytics compare-runs <run_a> <run_b>
python -m scripts.replay_analytics worst-cases <run_id> --top-k 10
python -m scripts.replay_analytics export-anomalies <run_id> logs/offline/anomalies.json
```

## Benchmark / latency contour
```bash
python -m scripts.cli ops benchmark --url https://datsblack.datsteam.dev/api/scan --samples 10
```
CLI печатает `connect/read/total` усреднения и `recommended_send_margin_ms`.

## Training-round playbook
Сценарий операторских действий: `docs/operations/training_round_playbook.md`.

## Contract-ready import prep (после релиза правил)
```bash
python -m scripts.prepare_datssol_import --tag 20260417T180000Z
```
См. `docs/operations/datssol_import_prep.md`.

## Важные ограничения
- не выдумываем DatsSol endpoints/schema/scoring/mechanics,
- не делаем fake implementation `games/datssol` beyond placeholders,
- не используем внешние LLM вызовы в hot path.
