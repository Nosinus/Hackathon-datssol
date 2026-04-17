# Open Questions for DatsSol Release

## P0 (blockers for first real live run)
1. Exact endpoint list and request/response schemas?
2. Required auth header and token provisioning flow?
3. Tick/request deadlines and timeout behavior?
4. Simultaneous or sequential action resolution?
5. Visibility model and hidden-information rules?
6. Scoring/tie-break rules and any private evaluation split?

## P1 (important for robust performance)
1. Retry/rate-limit behavior and explicit server error codes.
2. Whether commands can be overwritten in same tick.
3. Sandbox vs production environment split.
4. Constant drift risk between practice and finals.
5. Map retrieval format (if any map endpoint/file is provided).
6. Any server-provided replay that can be aligned with local `replay.v3` records.

## P2 (policy/compliance)
1. External model usage policy in live rounds.
2. Human-in-the-loop restrictions.
3. Any anti-cheat/autonomy enforcement details.

## Planned response once docs drop
- Keep `datsteam_core` transport/runtime generic; add only required contract deltas.
- Implement concrete `games/datssol` models/client/adapter from official docs only.
- Add official-schema fixtures + validator tests before first live submit.
- Keep DatsBlack exemplar for regression comparison, not as DatsSol truth.
- Add DatsSol-specific adapters for candidate generation/evaluation while preserving generic offline-lab interfaces.
