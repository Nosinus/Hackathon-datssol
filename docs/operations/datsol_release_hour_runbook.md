# DatsSol Release Hour Runbook (First 60 Minutes)

Goal: move from unknown DatsSol contract to a safe first live submission without guessing mechanics.

## T-0 to T+10 min — ingest official artifacts

1. Save official files under `docs/input/datssol_imports/` with explicit naming:
   - `docs/input/datssol_imports/openapi/<tag>_openapi.json` (if OpenAPI exists)
   - `docs/input/datssol_imports/rules/<tag>_official_rules.md` (manual summary)
2. Keep binaries (if any) in `docs/input/raw_binaries/` and add a short note in `docs/input/README.md`.
3. Do **not** change `src/games/datssol/` behavior yet.

## T+10 to T+20 min — contract extraction

1. Create/update truth artifacts:
   - `docs/contract/current_truth_table.md`
   - `docs/contract/current_truth_table.yaml`
   - `docs/contract/open_questions.md`
2. Mark each field as one of:
   - official contract,
   - exemplar inference (if any),
   - assumption.
3. Explicitly remove any assumptions invalidated by official docs.

## T+20 to T+35 min — adapter import scaffold

1. Add raw DatsSol models in `src/games/datssol/` directly from official schema.
2. Add typed client methods for official endpoints only.
3. Add canonical conversion layer and action validator.
4. Keep deterministic fallback strategy enabled even if baseline is minimal.

## T+35 to T+50 min — fixtures + smoke safety

1. Add minimal fixtures in `tests/fixtures/` from official examples:
   - state response,
   - action success,
   - action failure,
   - malformed payload case.
2. Add parser/validator defensive tests before live submit.
3. Run checks:
   - `python -m scripts.check_contract_consistency`
   - `python -m pytest -q`
   - `python -m ruff check src tests scripts`
   - `python -m mypy src`

## T+50 to T+60 min — legal baseline + first live dry run

1. Ensure baseline emits only validated actions.
2. Run dry/smoke command with minimal ticks and replay enabled.
3. Confirm logs capture:
   - tick/round metadata,
   - request outcome,
   - validator decisions.
4. Submit first live run only after all smoke checks pass.

## Exit criteria before first live submit

- no guessed DatsSol endpoints or schema fields in code
- deterministic fallback active
- contract docs aligned with imported official files
- parser/validator tests include malformed payload handling
- replay/log metadata enabled for debugging
