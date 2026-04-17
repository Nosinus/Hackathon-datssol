# Source Priority and Contract Semantics

This document defines the contract-first source-of-truth policy for this repository.

## Canonical input locations

- **Canonical text-first input folder:** `docs/input/`
- **Legacy binary archive folder:** `docs/input/archive/binaries/` (DOCX/PDF only; not canonical for markdown summaries)

## Priority order

1. **Official contract (highest priority)**
   - `docs/input/datsblack_openapi.json` for DatsBlack wire schema.
   - Future DatsSol official OpenAPI/spec files once imported into `docs/input/`.
2. **Curated markdown summaries**
   - `docs/input/*.md` summaries used for quick reasoning and onboarding.
3. **Raw binaries / archival material**
   - `docs/input/archive/binaries/*.docx`, `docs/input/archive/binaries/*.pdf` as backups when markdown is insufficient.
4. **Explicit assumptions**
   - `docs/contract/assumptions.md`, always treated as provisional.

## Terminology used in repo

- **Official contract**: machine-readable schema and endpoint definitions published by organizers (OpenAPI/JSON Schema/examples).
- **Exemplar**: concrete implemented prior used to validate architecture (currently DatsBlack only).
- **Transfer prior**: organizer-style behavioral hints from other games (e.g., Snake3D), not schema truth.
- **Assumption**: documented temporary hypothesis used only when official contract is absent.

## Guardrails

- Never infer DatsSol endpoints/mechanics from DatsBlack unless explicitly confirmed by DatsSol docs.
- DatsSol v1 contract is now imported; keep new unknowns limited to live operational behavior only.
- Update `docs/contract/current_truth_table.md` and `docs/contract/current_truth_table.yaml` together after each contract change.
