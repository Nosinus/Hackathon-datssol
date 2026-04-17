# Datsteam Competition Agent Starter (DatsSol v1 ready)

Репозиторий держит границы:
- **generic core**: `src/datsteam_core/`
- **DatsBlack exemplar**: `src/games/datsblack/`
- **DatsSol v1 adapter**: `src/games/datssol/`

## Что реализовано для DatsSol v1
- typed models/client для `GET /api/arena`, `POST /api/command`, `GET /api/logs`,
- canonical state + budget extraction из `nextTurnIn`,
- безопасный baseline (deterministic, expansion-first, upgrade-opportunistic),
- валидатор legal-action shape (`path`, `plantationUpgrade`, `relocateMain`),
- replay/summary совместимость с `code + errors` результатами.

## Быстрый старт
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
cp .env.example .env
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

## Самый безопасный smoke test
```bash
python -m scripts.cli datssol dry-run --fixture tests/fixtures/datssol/arena_sample.json
python -m scripts.cli datssol loop --dry-run --ticks 3 --fixture tests/fixtures/datssol/arena_sample.json
python -m scripts.summarize_replay logs/replay
```

## Live probes
```bash
python -m scripts.cli datssol arena
python -m scripts.cli datssol logs
```

## Команда из файла
```bash
python -m scripts.cli datssol command --from-file payload.json
```
