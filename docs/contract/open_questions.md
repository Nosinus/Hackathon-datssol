# Open Questions (post DatsSol v1 import)

DatsSol schema is no longer unknown. Remaining questions are **operational/live**:

## P0
1. Exact server throttling/rate limits for `/api/arena`, `/api/command`, `/api/logs`.
2. Whether duplicate `POST /api/command` in one turn is strictly rejected in all environments.
3. Whether skipping submit in a turn has any hidden penalty beyond no action.

## P1
1. Full enum space for `meteoForecasts.kind` in live rounds.
2. Any additional error codes/messages beyond documented samples.
3. Whether `GET /api/logs` is always list-shaped for registered players.

## P2
1. Final-round timing/turn duration changes after training.
2. Any late balancing changes to upgrade caps or hazard probabilities.

## Stage-1 still-open live checks

- Exact duplicate-submit behavior across race conditions (same turn, delayed ACK).
- Whether `GET /api/logs` may truncate or paginate under long rounds.
