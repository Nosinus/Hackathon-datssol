# DatsSol contract import prep

## Canonical location
Put release artifacts in `docs/input/datssol_imports/`.

## Naming convention
Use a release tag (UTC), e.g. `20260417T180000Z`:
- `rules/{tag}_official_rules.md`
- `openapi/{tag}_openapi.json`
- `examples/{tag}_examples.json`
- `notes/{tag}_release_notes.md`
- `screenshots/{tag}_doc_capture.png`
- `{tag}_import_checklist.json` (generated helper)

## Helper
```bash
python -m scripts.prepare_datssol_import --tag 20260417T180000Z
```

## Import checklist
1. Save official docs text snapshot (`rules/`).
2. Save official OpenAPI snapshot (`openapi/`).
3. Save representative request/response examples (`examples/`).
4. Save screenshots and notes (`screenshots/`, `notes/`).
5. Update `docs/contract/current_truth_table.md` + `.yaml`.
6. Add fixtures under `tests/fixtures/datssol/`.
7. Run smoke checks (`pytest`, `ruff`, `mypy`, fixture run).

This prep does **not** implement DatsSol mechanics before official release.
