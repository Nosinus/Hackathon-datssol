# Training-round playbook

## First hour checklist
1. Create explicit run manifest.
2. Run one dry-run fixture loop to verify telemetry path.
3. Run benchmark against target endpoint.
4. Run one short live-safe baseline (or dry-run if network unavailable).
5. Ingest replay files into SQLite and inspect summary.

## Run types
- **Contract probing:** minimal safe requests to discover schema/errors.
- **Baseline farming:** stable deterministic policy to gather broad telemetry.
- **Hypothesis testing:** limited controlled parameter changes per run.

## Avoid wasting rounds
- Never mix multiple major changes in one run.
- Keep `policy_id` and `mode` explicit in each manifest.
- Always attach replay and manifest to run notes.

## Required artifacts after each run
- run manifest JSON (`ops/manifests/*.json`),
- raw replay files (`logs/replay/*.json`),
- SQLite ingest snapshot (`logs/analytics/replays.sqlite`),
- post-run summary JSON (single-run + worst-cases export).

## Minimum metrics between runs
- avg/median latency and transport errors,
- fallback count,
- invalid/sanitized action count,
- unknown-field count,
- low-margin decisions,
- disagreement bucket count (if present in parser extras).

## Quick command chain
```bash
python -m scripts.cli ops create-manifest --output ops/manifests/run_a.json --policy-id safe_baseline --mode training --environment local
python -m scripts.cli datsblack loop --dry-run --ticks 5 --manifest ops/manifests/run_a.json
python -m scripts.replay_analytics ingest --replay-dir logs/replay --manifest-dir ops/manifests
python -m scripts.replay_analytics summarize-run $(jq -r '.run_id' ops/manifests/run_a.json)
python -m scripts.replay_analytics worst-cases $(jq -r '.run_id' ops/manifests/run_a.json)
```
