# DatsSol local live quickstart (PowerShell)

## Что запускать прямо сейчас

```powershell
cd C:\path\to\Hackathon-datssol
.\.venv\Scripts\Activate.ps1
python -m scripts.cli datssol doctor
python -m scripts.cli datssol once
```

Если нужно непрерывно крутить цикл:

```powershell
python -m scripts.cli datssol loop --ticks 200
```

Остановить цикл: `Ctrl+C`.

## Базовый локальный setup (без Docker)

```powershell
cd C:\path\to\Hackathon-datssol
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
Copy-Item .env.example .env
```

## Замороженный env-контракт (совместимость)

Обязательные существующие переменные, которые уже работают:

- `DATASTEAM_GAME=datssol`
- `DATASTEAM_API_BASE_URL=https://games-test.datsteam.dev`
- `DATASTEAM_AUTH_HEADER=X-Auth-Token`
- `DATASTEAM_API_KEY=<token>`
- `DATASTEAM_TIMEOUT_SECONDS=5.0`
- `DATASTEAM_RETRIES=1`
- `DATASTEAM_REPLAY_DIR=logs/replay`
- `DATASTEAM_BACKOFF_INITIAL_SECONDS=0.2`
- `DATASTEAM_BACKOFF_MULTIPLIER=2.0`
- `DATASTEAM_BACKOFF_MAX_SECONDS=1.0`
- `DATASTEAM_ACCEPT_GZIP=true`
- `DATASTEAM_SEND_MARGIN_MS=100`

Опциональные timeout override (можно не задавать):

- `DATASTEAM_HOT_TIMEOUT_SECONDS`
- `DATASTEAM_COLD_TIMEOUT_SECONDS`
- `DATASTEAM_ARENA_TIMEOUT_SECONDS`
- `DATASTEAM_COMMAND_TIMEOUT_SECONDS`
- `DATASTEAM_LOGS_TIMEOUT_SECONDS`

## Smoke-команды

```powershell
python -m scripts.cli datssol arena
python -m scripts.cli datssol logs
python -m scripts.cli datssol watch --ticks 20
python -m scripts.cli datssol submit --file payload.json --dry-run
```

## Где смотреть логи

- `logs/live/latest_arena.json`
- `logs/live/latest_logs.json`
- `logs/live/command_history.ndjson`
- `logs/live/errors.ndjson`
- `logs/replay/`

## Если arena пустая (`size=[0,0]`)

Это штатно для idle-состояния. Бот не отправляет пустые команды и ждёт активного тика.

## Если в logs видно `not registered`

1. Проверьте `DATASTEAM_API_KEY` и `DATASTEAM_AUTH_HEADER`.
2. Проверьте `DATASTEAM_API_BASE_URL`.
3. Запустите `python -m scripts.cli datssol doctor` и убедитесь, что `token_loaded=true`.

## Если пришло `command already submitted this turn`

- В live-loop уже есть защита от duplicate submit по `turnNo`.
- Если вручную отправляли команды параллельно, остановите лишние процессы и оставьте один loop.
