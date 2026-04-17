# Implemented vs Unknown

## Implemented now (real, testable)

### Generic core (`src/datsteam_core/`)
- runtime supports `tickRemainMs` **and** `nextTurnIn` budget extraction
- replay success inference supports both `success` and `code/errors`
- transport includes `get_json()` for list-or-object endpoints (used by DatsSol logs)
- neutral fallback payload no longer assumes `{"commands": []}`

### DatsSol v1 (`src/games/datssol/`)
- typed raw models for arena/command/logs payload families
- typed API client for `/api/arena`, `/api/command`, `/api/logs`
- canonical mapper with preserved unknown fields
- legal validator for command paths, upgrade, relocateMain
- deterministic expansion-first baseline strategy
- live adapter + CLI support + dry-run fixture path

### DatsBlack exemplar (`src/games/datsblack/`)
- unchanged as reference implementation and regression surface

## Still unknown / live-verification needed
- exact rate limiting / duplicate-submit behavior under load
- full live semantics for when skipping submit is preferable vs harmful
- complete server-side logs schema variants across all failure modes

## Deliberately not implemented
- speculative deep search / MCTS for DatsSol v1
- external LLM calls in live action path
- hardcoded token or environment secrets

### Stage-1 additions

- datssol graph/connectivity summary and articulation risk extraction are implemented.
- datssol semantic validator rejects empty payloads and range-invalid paths.
- datssol exit scheduler penalizes repeated exit usage within shortlist scheduling.
