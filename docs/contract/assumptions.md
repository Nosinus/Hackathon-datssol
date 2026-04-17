# Assumptions (narrow, explicit)

## A1. Generic runtime contract
Assume Datsteam competitions continue to use HTTP/JSON tick loops with authenticated requests.

## A2. DatsBlack is exemplar only
Assume DatsBlack can validate architecture and quality, but **not** final DatsSol mechanics.

## A3. Conservative baseline policy
Assume safe deterministic behavior (valid actions, low-risk movement, no default risky shots) is the correct baseline before optimization.

## A4. Offline-first validation
Assume live game servers may be unreachable from coding environment; therefore fixture-driven tests and replay outputs are mandatory.

## A5. Parameter drift is normal
Assume final game constants can differ from test/prototype values; avoid hard-coding unstable constants in core.

## A6. Unknowns isolated in adapter boundary
Assume schema/auth/time-budget unknowns for DatsSol should remain in placeholder interfaces and open-question docs until official release.

## A7. Canonical source locations
Assume `docs/input/` is canonical for text/contract snapshots while `docs/input/raw_binaries/` is archival binary-only storage.

## A8. Offline decision lab assumption
Assume policy quality should be improved primarily through deterministic replay/manifests and comparable metrics before any live experimentation.
