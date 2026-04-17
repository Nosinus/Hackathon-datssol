# DatsSol v1 Runbook

## Safe startup checklist
1. Export env (`DATASTEAM_API_BASE_URL`, `DATASTEAM_AUTH_HEADER=X-Auth-Token`, token).
2. Run offline dry-run loop and verify replay write.
3. Probe live read-only endpoints:
   - `python -m scripts.cli datssol arena`
   - `python -m scripts.cli datssol logs`
4. Only then send a command from a reviewed JSON file:
   - `python -m scripts.cli datssol command --from-file <payload.json>`

## Live safety notes
- Do not send empty action payloads to `/api/command`.
- Handle `command already submitted this turn` gracefully.
- Prioritize HQ survival and avoid over-limit builds that can delete the oldest plantation.

## Verification commands
```bash
python -m pytest -q
python -m ruff check src tests scripts
python -m mypy src
```
