# Current Truth Table (as of April 17, 2026, DatsSol v1 import)

Machine-readable mirror: `docs/contract/current_truth_table.yaml`.

| Topic | Known now | Confidence | Source basis |
|---|---|---|---|
| DatsSol loop style | HTTP/JSON, server-authoritative, tick/turn based | High | `docs/input/Документация ИГРЫ.docx` |
| DatsSol auth | `X-Auth-Token` header | High | `docs/input/Документация ИГРЫ.docx` |
| DatsSol endpoints | `GET /api/arena`, `POST /api/command`, `GET /api/logs` | High | `docs/input/Документация ИГРЫ.docx` |
| DatsSol budget field | `nextTurnIn` seconds until next turn | High | `docs/input/Документация ИГРЫ.docx` |
| DatsSol command response | `code` + `errors[]` (not `success: bool`) | High | `docs/input/Документация ИГРЫ.docx` |
| DatsSol arena entities | plantations/enemy/mountains/cells/construction/beavers/upgrades/meteo | High | `docs/input/Документация ИГРЫ.docx` |
| DatsSol action shape | `command[].path=[author, output, target]`, optional `plantationUpgrade`, optional `relocateMain` | High | `docs/input/Документация ИГРЫ.docx` |
| Empty command behavior | May return empty-command error if no useful action supplied | High | `docs/input/Документация ИГРЫ.docx` |
| Turn and round timing | 1 second turn (documented), 600 turns per round | Medium | `docs/input/Документация ИГРЫ.docx` |
| Victory tiebreakers | points, then fewer lost plantations, then more beaver lairs destroyed, then more sabotages | High | `docs/input/Документация ИГРЫ.docx` |
| DatsBlack exemplar | Fully implemented and retained for regression/reference | High | implementation in repo |

## Purpose

- DatsSol schema is now concrete in code/docs.
- Keep generic runtime + adapter split.
- Track only remaining real ambiguities in `open_questions.md`.

## Stage-1 implementation checkpoint (2026-04-17)

- `src/games/datssol/` now includes concrete legality, scheduling, scoring, and fallback modules.
- Replay and CLI paths preserve semantic success distinction (`code==0` with empty `errors[]` required).
