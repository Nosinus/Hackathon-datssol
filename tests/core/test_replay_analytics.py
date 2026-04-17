from __future__ import annotations

import json
from pathlib import Path

from scripts import replay_analytics


def _write_tick(
    path: Path,
    *,
    run_id: str,
    tick: int,
    margin: float | None = None,
    fallback_used: bool | None = None,
    fallback_flags: dict[str, bool] | None = None,
) -> None:
    payload: dict[str, object] = {
        "schema_version": "replay.v3",
        "session_id": "s1",
        "round_id": "r1",
        "turn_id": tick,
        "server_tick": tick,
        "state_hash": "h",
        "strategy_id": "safe",
        "action_reason": "x",
        "request_payload": {},
        "response_payload": {"success": True},
        "canonical_state": {"tick": tick, "me": [], "enemies": [], "metadata": {}},
        "chosen_action": {"payload": {"commands": []}, "reason": "noop"},
        "validator_result": {},
        "request_meta": {},
        "response_meta": {},
        "fallback_used": tick % 2 == 0 if fallback_used is None else fallback_used,
        "fallback_flags": fallback_flags or {},
        "candidate_scores": (
            [{"score": 1.0}, {"score": 1.0 - margin}] if margin is not None else []
        ),
        "latency_ms": 20 + tick,
        "validation_flags": {"sanitized": tick == 1},
        "parser_extras": {"unknown_fields": ["u"] if tick == 1 else []},
        "run_metadata": {"run_id": run_id, "session_id": "s1", "policy_id": "safe_baseline"},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_ingest_and_summarize_run(tmp_path: Path) -> None:
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir()
    _write_tick(replay_dir / "tick_000001_a.json", run_id="run-1", tick=1, margin=0.01)
    _write_tick(replay_dir / "tick_000002_b.json", run_id="run-1", tick=2, margin=0.2)

    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    (manifest_dir / "run-1.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "session_id": "s1",
                "policy_id": "safe_baseline",
                "config_hash": "cfg",
                "git_sha": "sha",
                "mode": "training",
                "environment": "local",
                "created_at": "2026-01-01T00:00:00Z",
                "replay_dir": "logs/replay",
            }
        ),
        encoding="utf-8",
    )

    db = tmp_path / "analytics.sqlite"
    ingest_payload = replay_analytics.ingest(replay_dir, manifest_dir, db)
    assert ingest_payload["inserted_ticks"] == 2

    summary = replay_analytics.summarize_run(db, "run-1")
    assert summary["ticks"] == 2
    assert summary["fallback_count"] == 1
    assert summary["unknown_field_count"] == 1
    assert summary["low_margin_count"] == 1


def test_ingest_counts_fallback_flags_when_top_level_flag_is_false(tmp_path: Path) -> None:
    replay_dir = tmp_path / "replay"
    replay_dir.mkdir()
    _write_tick(
        replay_dir / "tick_000001_a.json",
        run_id="run-flag-fallback",
        tick=1,
        fallback_used=False,
        fallback_flags={"send_margin_safe_hold": True},
    )

    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    db = tmp_path / "analytics.sqlite"

    replay_analytics.ingest(replay_dir, manifest_dir, db)
    summary = replay_analytics.summarize_run(db, "run-flag-fallback")

    assert summary["ticks"] == 1
    assert summary["fallback_count"] == 1
