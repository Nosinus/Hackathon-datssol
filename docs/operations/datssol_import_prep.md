# DatsSol contract import prep (historical + incremental updates)

## Canonical location
Put release artifacts in `docs/input/datssol_imports/`.

## Naming convention
Use a release tag (UTC), e.g. `20260417T180000Z`:
- `{tag}_event_notes.md`
- `{tag}_openapi.json`
- `{tag}_examples.json`
- `{tag}_extra_notes.md`
- `{tag}_import_checklist.json` (generated helper)

## Helper
```bash
python -m scripts.prepare_datssol_import --tag 20260417T180000Z
```

## Import checklist
1. Save official docs text snapshot.
2. Save official OpenAPI snapshot.
3. Save representative request/response examples.
4. Update `docs/contract/current_truth_table.md` + `.yaml`.
5. Add fixtures under `tests/fixtures/datssol/`.
6. Run smoke checks (`pytest`, `ruff`, `mypy`, fixture run).

The initial release import is complete; use this checklist for future contract updates.
Дополнительный handoff-чеклист: `docs/dev/release_hour_import.md`.
