# Datsteam Competition Agent Starter (DatsSol live-stable)

Репозиторий держит границы:
- **generic core**: `src/datsteam_core/`
- **DatsBlack exemplar**: `src/games/datsblack/`
- **DatsSol adapter**: `src/games/datssol/`

## DatsSol live: замороженный env-контракт (совместимость сохранена)
Существующие переменные продолжают работать **без переименований и без изменения смысла**:

- `DATASTEAM_GAME`
- `DATASTEAM_API_BASE_URL`
- `DATASTEAM_AUTH_HEADER`
- `DATASTEAM_API_KEY`
- `DATASTEAM_TIMEOUT_SECONDS`
- `DATASTEAM_RETRIES`
- `DATASTEAM_REPLAY_DIR`
- `DATASTEAM_BACKOFF_INITIAL_SECONDS`
- `DATASTEAM_BACKOFF_MULTIPLIER`
- `DATASTEAM_BACKOFF_MAX_SECONDS`
- `DATASTEAM_ACCEPT_GZIP`
- `DATASTEAM_SEND_MARGIN_MS`

Дополнительные переменные добавлены только как **опциональные override**:

- `DATASTEAM_HOT_TIMEOUT_SECONDS`
- `DATASTEAM_COLD_TIMEOUT_SECONDS`
- `DATASTEAM_ARENA_TIMEOUT_SECONDS`
- `DATASTEAM_COMMAND_TIMEOUT_SECONDS`
- `DATASTEAM_LOGS_TIMEOUT_SECONDS`

Если override не заданы, поведение остаётся безопасным и обратно-совместимым.

## Что запускать локально

```bash
python -m scripts.cli datssol doctor
python -m scripts.cli datssol arena
python -m scripts.cli datssol logs
python -m scripts.cli datssol once
python -m scripts.cli datssol loop --ticks 10
```

Дополнительно:

```bash
python -m scripts.cli datssol watch --ticks 20
python -m scripts.cli datssol submit --file payload.json --dry-run
python -m scripts.cli datssol submit --file payload.json
```

## Live safety defaults

- hot path (`/api/arena`, `/api/command`) использует малый timeout (обычно около `0.35–0.60s`),
- cold path (`/api/logs`) может работать с более длинным timeout,
- пустые payload не отправляются в `/api/command`,
- есть guard от повторной отправки в тот же `turnNo` в live loop,
- idle arena (`size=[0,0]` или нет plantations) обрабатывается без мусорных submit.

## Telemetry и артефакты

- `logs/live/latest_arena.json`
- `logs/live/latest_logs.json`
- `logs/live/command_history.ndjson`
- `logs/live/errors.ndjson`
- replay envelopes: `logs/replay/`

## Проверки

```bash
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```

## PowerShell-ориентированный гайд

См. `docs/operations/local_live_quickstart.md`.
