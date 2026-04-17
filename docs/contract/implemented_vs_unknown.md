# Implemented vs Unknown

## Implemented now (real, testable)

### Generic core (`src/datsteam_core/`)
- typed config loading (env + yaml)
- auth header abstraction
- HTTP transport with timeout/retry and schema/status error classes
- canonical runtime interfaces and runtime loop
- replay writer and replay summary
- fixture evaluator scaffold

### DatsBlack exemplar (`src/games/datsblack/`)
- typed raw models aligned to DatsBlack OpenAPI
- API client for map/scan/longScan/shipCommand/registration/exit endpoints
- canonicalization from raw payloads into internal canonical state
- legal action sanitizer and deterministic safe baseline strategy
- live entrypoint and offline fixture scripts
- fixture coverage for lifecycle responses + defensive parser behavior

## DatsBlack-only scope (must not be generalized blindly)

The following are exemplar-specific and intentionally isolated:
- endpoint names and route structure (`/api/scan`, `/api/shipCommand`, ...)
- auth header `X-API-Key`
- fleet entities (`myShips`, `enemyShips`, `zone`, `tick`)
- per-ship command schema (`changeSpeed`, `rotate`, `cannonShoot`)
- mode-specific registration (`deathMatch`, `royalBattle`)

## DatsSol unknowns (still intentionally unresolved)

- actual endpoint set and schemas
- auth header/token flow
- timing budgets and deadline semantics
- scoring and tie-break details
- visibility model and hidden-information behavior
- rate limits, env split (practice/prod), and server quirks
- compliance constraints for tooling/model usage during live rounds

See also: `docs/contract/open_questions.md`.

## Deliberately not implemented

- guessed `games/datssol` mechanics or endpoints
- DatsBlack logic copied into DatsSol adapter
- live external LLM calls in runtime action path
- speculative framework rewrites unrelated to contract correctness
