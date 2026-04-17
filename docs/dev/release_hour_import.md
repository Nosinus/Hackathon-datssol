# Release-hour import (DatsSol)

Status: completed for v1 in this repository (April 17, 2026).

## Imported contract surface
- auth: `X-Auth-Token`
- endpoints: `/api/arena`, `/api/command`, `/api/logs`
- turn budget: `nextTurnIn`
- command response: `code` + `errors[]`

## Current minimum safe flow
```bash
python -m scripts.cli datssol dry-run --fixture tests/fixtures/datssol/arena_sample.json
python -m scripts.cli datssol loop --dry-run --ticks 3 --fixture tests/fixtures/datssol/arena_sample.json
python -m scripts.summarize_replay logs/replay
```

## Before first real live submit
1. Confirm token and base URL from env/config only.
2. Probe `/api/arena` and `/api/logs` once.
3. Send only validated command payloads; never send empty command bodies.
