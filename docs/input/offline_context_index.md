# Offline context pack for Codex — Datsteam / DatsSol prep (v2)

This pack exists because Codex is expected to work **without internet access** tonight.
The goal is to convert the current mixed context (web pages, PDF, DOCX, OpenAPI) into text-first files that Codex can consume quickly.

## What this pack is for

Use these files to bootstrap a repository that is:

- generic enough for an unknown upcoming Datsteam HTTP/JSON competition,
- concrete enough to produce a runnable baseline using **DatsBlack** as the most detailed prior,
- easy to retarget once the real DatsSol rules arrive.

## Read order for Codex

1. `docs/input/offline_context_index.md` — this file.
2. `docs/input/datssol_event_snapshot_2026-04-16.md` — what is publicly known about the upcoming event.
3. `docs/input/datsteam_architecture_implications_for_codex.md` — distilled engineering consequences across all sources.
4. `docs/input/datsblack_truth_table_and_mechanics.md` — the richest prior for a real Datsteam competition loop.
5. `docs/input/datsblack_openapi_reference.md` — wire-level contract summary extracted from `datsblack_openapi.json`.
6. `docs/input/snake3d_warmup_summary.md` — organizer-style prior from the warm-up game.
7. `docs/input/research_memo_highlights.md` — condensed guidance from the research memo.
8. `docs/input/questions_for_datsol_release.md` — what is still missing and must stay isolated behind interfaces.
9. Raw source files only if needed:
   - `datsblack_openapi.json`
   - `Геймтон DatsBlack .docx`
   - `doc.pdf`
   - `Исследование стратегии участия в HTTP_JSON-соревновании агентов.docx`

## How Codex should interpret the sources

### Source priority
1. `datsblack_openapi.json` is the **wire-contract source of truth** for DatsBlack request/response shapes.
2. The markdown files in this pack are the **fastest human-curated summaries**.
3. The raw DOCX/PDF files are **reference backups**, not the first thing to parse.
4. Public DatsSol event information is **metadata only**, not a mechanics contract.

### Working assumptions
- The real DatsSol gameplay rules are still unknown.
- The public DatsSol event page confirms the HTTP/JSON gameplay loop and release schedule, but not the game schema.
- DatsBlack is the best currently available fully specified prior.
- Snake3D is a transfer prior for organizer style and server interaction patterns, not proof of final mechanics.

## What Codex should build tonight

Build **two things at once**:

1. A **generic Datsteam competition core**
   - config
   - HTTP transport
   - auth abstraction
   - typed raw payload models
   - canonical state models
   - replay / telemetry logging
   - deterministic fallback
   - strategy interface
   - evaluator / fixture runner
   - tests

2. A **concrete DatsBlack adapter**
   - typed client from the available contract
   - map / scan / command models
   - canonicalization for ships / zone / visibility
   - safe baseline policy
   - fixture-based tests
   - docs on what is concrete vs what remains provisional for DatsSol

## Hard constraints for Codex

- No live LLM call in the runtime path by default.
- Do not assume the cloud environment can reach the actual game servers.
- Use fixtures and offline validation; do not block on live network checks.
- Keep DatsBlack-specific logic behind an adapter.
- Keep DatsSol-specific unknowns behind TODOs and interfaces, not hard-coded guesses.
- Prefer small, testable, typed modules over speculative frameworks.

## Minimal overnight success criteria

By morning, the repo should have:

- a coherent structure,
- a runnable local baseline path using fixtures,
- a replay/logging path,
- a deterministic fallback,
- contract docs,
- tests,
- a clear list of DatsSol unknowns,
- a DatsBlack example adapter that proves the architecture is real.

## Suggested placement

Copy the markdown files in this folder into `docs/input/` of the repo.
Place `AGENTS_datsteam_template_v2.md` into the repo root as `AGENTS.md`.
Use either prompt file from `prompts/` when launching Codex.
