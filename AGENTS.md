# AGENTS.md — Datsteam competition repo bootstrap (v2)

## Start here

Read these files in order before major edits:

1. `docs/input/offline_context_index.md`
2. `docs/input/datssol_event_snapshot_2026-04-16.md`
3. `docs/input/datsteam_architecture_implications_for_codex.md`
4. `docs/input/datsblack_truth_table_and_mechanics.md`
5. `docs/input/datsblack_openapi_reference.md`
6. `docs/input/snake3d_warmup_summary.md`
7. `docs/input/research_memo_highlights.md`
8. `docs/input/questions_for_datsol_release.md`
9. `docs/input/openapi.json`
10. raw binaries only if needed

If a markdown summary exists, prefer it over parsing the DOCX/PDF first.

## Repository mission

This repository is a production-oriented starter kit for a Datsteam-style HTTP/JSON competition agent.

It must produce:
- a **generic competition core**,
- a **concrete DatsBlack exemplar adapter**,
- clearly isolated **DatsSol placeholders** for what is still unknown.

The point is not to overfit to a single warm-up game.
The point is to wake up with a repository that is runnable, testable, and easy to retarget.

## Source priority

1. `docs/input/openapi.json` for DatsBlack wire-contract truth
2. curated markdown files in `docs/input/`
3. raw source binaries in `docs/input/`
4. generic assumptions only after the above

Treat:
- DatsSol public event info as **metadata**, not schema truth
- DatsBlack as the **best concrete exemplar**
- Snake3D as a **transfer prior**
- the research memo as the **design brief**

## Engineering priorities

1. Valid and deterministic runtime
2. Transport and schema correctness
3. Replay / telemetry / evaluator
4. Clear adapter boundaries
5. Safe baseline strategy
6. Tests and docs
7. Nice-to-have tooling later

## Runtime rules

- Do not put external LLM calls into the live action path by default.
- Always preserve a deterministic fallback action.
- Never emit unvalidated JSON to the game server.
- Keep raw payload models separate from canonical internal state.
- Prefer explicit typed models over loose dict plumbing.
- Do not assume live network access to game servers inside the Codex environment.

## Architecture rules

- Isolate game-specific logic behind adapters.
- Keep transport, validation, legality, fallback, metrics, and release gating in code.
- Keep files small and modular.
- Prefer practical, testable abstractions over speculative frameworks.
- Use DatsBlack to prove the architecture concretely.
- Keep DatsSol unknowns behind TODOs / interfaces, not guesses.

## Required docs

Keep these up to date when behavior changes:

- `README.md`
- `docs/contract/current_truth_table.md`
- `docs/contract/assumptions.md`
- `docs/contract/open_questions.md`
- `docs/strategy/preliminary_strategy.md`
- `docs/strategy/runtime_vs_offline.md`
- `docs/dev/quickstart.md`
- `docs/dev/backlog.md`

## Verification rules

Before considering a task complete:

- run tests relevant to the changed code,
- run lint / format / type checks if configured,
- update docs for any changed behavior,
- review your diff for regressions and unnecessary edits.

## Done means

A task is done only when:
- code is runnable,
- assumptions are documented,
- tests cover the important path,
- the change is explained in docs or summary,
- the repo remains easy for a human teammate to continue,
- the difference between generic core / DatsBlack exemplar / DatsSol unknowns is clear.

## What to avoid

- giant rewrites,
- premature optimization,
- hidden magic,
- undocumented assumptions,
- unrelated refactors,
- runtime dependence on cloud models,
- pretending DatsBlack is already DatsSol.
