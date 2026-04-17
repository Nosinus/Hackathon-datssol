from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TickRow:
    run_id: str
    session_id: str
    policy_id: str
    tick: int
    latency_ms: int | None
    fallback_used: int
    invalid_or_sanitized: int
    unknown_field_count: int
    disagreement_bucket: int
    top_margin: float | None
    transport_error: int
    source_file: str


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
          run_id TEXT PRIMARY KEY,
          session_id TEXT,
          policy_id TEXT,
          config_hash TEXT,
          git_sha TEXT,
          mode TEXT,
          environment TEXT,
          created_at TEXT,
          replay_dir TEXT,
          manifest_path TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS replay_ticks (
          run_id TEXT,
          session_id TEXT,
          policy_id TEXT,
          tick INTEGER,
          latency_ms INTEGER,
          fallback_used INTEGER,
          invalid_or_sanitized INTEGER,
          unknown_field_count INTEGER,
          disagreement_bucket INTEGER,
          top_margin REAL,
          transport_error INTEGER,
          source_file TEXT PRIMARY KEY
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ticks_run_id ON replay_ticks(run_id)")
    return conn


def _collect_manifests(manifest_dir: Path) -> dict[str, tuple[dict[str, Any], Path]]:
    if not manifest_dir.exists():
        return {}
    out: dict[str, tuple[dict[str, Any], Path]] = {}
    for path in sorted(manifest_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            continue
        run_id = payload.get("run_id")
        if isinstance(run_id, str) and run_id:
            out[run_id] = (payload, path)
    return out


def _top_margin(payload: dict[str, Any]) -> float | None:
    scores = payload.get("candidate_scores")
    if not isinstance(scores, list) or len(scores) < 2:
        return None
    first = scores[0]
    second = scores[1]
    if not isinstance(first, dict) or not isinstance(second, dict):
        return None
    s1 = first.get("score")
    s2 = second.get("score")
    if not isinstance(s1, int | float) or not isinstance(s2, int | float):
        return None
    return float(s1 - s2)


def _to_row(path: Path, payload: dict[str, Any]) -> TickRow:
    run_meta = payload.get("run_metadata")
    run_meta = run_meta if isinstance(run_meta, dict) else {}

    unknown_fields = payload.get("parser_extras", {})
    unknown_fields = unknown_fields if isinstance(unknown_fields, dict) else {}
    unknown = unknown_fields.get("unknown_fields")

    flags = payload.get("validation_flags", {})
    flags = flags if isinstance(flags, dict) else {}
    fallback_flags = payload.get("fallback_flags", {})
    fallback_flags = fallback_flags if isinstance(fallback_flags, dict) else {}

    run_id = run_meta.get("run_id")
    if not isinstance(run_id, str) or not run_id:
        run_id = f"session:{payload.get('session_id', 'unknown')}"
    session_id = run_meta.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        session_id = str(payload.get("session_id", "unknown"))

    policy_id = run_meta.get("policy_id")
    if not isinstance(policy_id, str) or not policy_id:
        policy_id = str(payload.get("strategy_id", "unknown_strategy"))

    disagreement = 0
    if bool(unknown_fields.get("policy_disagreement", False)):
        disagreement = 1
    fallback_used = bool(payload.get("fallback_used", False))
    if not fallback_used:
        fallback_used = any(bool(v) for v in fallback_flags.values())

    return TickRow(
        run_id=run_id,
        session_id=session_id,
        policy_id=policy_id,
        tick=int(payload.get("server_tick", payload.get("turn_id", 0))),
        latency_ms=payload.get("latency_ms")
        if isinstance(payload.get("latency_ms"), int)
        else None,
        fallback_used=1 if fallback_used else 0,
        invalid_or_sanitized=1 if bool(flags.get("sanitized", False)) else 0,
        unknown_field_count=len(unknown) if isinstance(unknown, list) else 0,
        disagreement_bucket=disagreement,
        top_margin=_top_margin(payload),
        transport_error=1 if isinstance(payload.get("transport_error"), dict) else 0,
        source_file=str(path),
    )


def ingest(replay_dir: Path, manifest_dir: Path, db_path: Path) -> dict[str, object]:
    manifests = _collect_manifests(manifest_dir)
    files = sorted(replay_dir.glob("tick_*.json"))

    conn = _connect(db_path)
    inserted = 0
    runs_seen: set[str] = set()

    with conn:
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                continue
            row = _to_row(path, payload)
            runs_seen.add(row.run_id)
            conn.execute(
                """
                INSERT OR REPLACE INTO replay_ticks (
                  run_id, session_id, policy_id, tick, latency_ms, fallback_used,
                  invalid_or_sanitized, unknown_field_count, disagreement_bucket,
                  top_margin, transport_error, source_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.run_id,
                    row.session_id,
                    row.policy_id,
                    row.tick,
                    row.latency_ms,
                    row.fallback_used,
                    row.invalid_or_sanitized,
                    row.unknown_field_count,
                    row.disagreement_bucket,
                    row.top_margin,
                    row.transport_error,
                    row.source_file,
                ),
            )
            inserted += 1

        for run_id in runs_seen:
            manifest_pair = manifests.get(run_id)
            if manifest_pair is None:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO runs (
                      run_id, session_id, policy_id, config_hash, git_sha, mode,
                      environment, created_at, replay_dir, manifest_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, None, None, None, None, None, None, None, str(replay_dir), None),
                )
                continue

            manifest, mpath = manifest_pair
            conn.execute(
                """
                INSERT OR REPLACE INTO runs (
                  run_id, session_id, policy_id, config_hash, git_sha, mode,
                  environment, created_at, replay_dir, manifest_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.get("run_id"),
                    manifest.get("session_id"),
                    manifest.get("policy_id"),
                    manifest.get("config_hash"),
                    manifest.get("git_sha"),
                    manifest.get("mode"),
                    manifest.get("environment"),
                    manifest.get("created_at"),
                    manifest.get("replay_dir"),
                    str(mpath),
                ),
            )

    return {"db": str(db_path), "inserted_ticks": inserted, "runs_seen": sorted(runs_seen)}


def _aggregate(conn: sqlite3.Connection, run_id: str) -> dict[str, object]:
    row = conn.execute(
        """
        SELECT
          COUNT(*) AS ticks,
          AVG(latency_ms) AS latency_avg,
          SUM(fallback_used) AS fallback_count,
          SUM(invalid_or_sanitized) AS invalid_or_sanitized_count,
          SUM(unknown_field_count) AS unknown_field_count,
          SUM(disagreement_bucket) AS disagreement_bucket_count,
          SUM(transport_error) AS transport_error_count,
          SUM(
            CASE WHEN top_margin IS NOT NULL AND top_margin <= 0.05 THEN 1 ELSE 0 END
          ) AS low_margin_count
        FROM replay_ticks
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchone()
    if row is None:
        return {"run_id": run_id, "ticks": 0}

    run_row = conn.execute(
        (
            "SELECT session_id, policy_id, config_hash, git_sha, mode, environment "
            "FROM runs WHERE run_id = ?"
        ),
        (run_id,),
    ).fetchone()
    return {
        "run_id": run_id,
        "session_id": run_row[0] if run_row else None,
        "policy_id": run_row[1] if run_row else None,
        "config_hash": run_row[2] if run_row else None,
        "git_sha": run_row[3] if run_row else None,
        "mode": run_row[4] if run_row else None,
        "environment": run_row[5] if run_row else None,
        "ticks": row[0] or 0,
        "latency_avg_ms": float(row[1]) if row[1] is not None else None,
        "fallback_count": row[2] or 0,
        "invalid_or_sanitized_count": row[3] or 0,
        "unknown_field_count": row[4] or 0,
        "disagreement_bucket_count": row[5] or 0,
        "transport_error_count": row[6] or 0,
        "low_margin_count": row[7] or 0,
    }


def summarize_run(db_path: Path, run_id: str) -> dict[str, object]:
    conn = _connect(db_path)
    return _aggregate(conn, run_id)


def compare_runs(db_path: Path, run_a: str, run_b: str) -> dict[str, object]:
    conn = _connect(db_path)
    left = _aggregate(conn, run_a)
    right = _aggregate(conn, run_b)
    return {
        "run_a": left,
        "run_b": right,
        "delta": {
            "latency_avg_ms": (left.get("latency_avg_ms") or 0)
            - (right.get("latency_avg_ms") or 0),
            "fallback_count": (left.get("fallback_count") or 0)
            - (right.get("fallback_count") or 0),
            "invalid_or_sanitized_count": (left.get("invalid_or_sanitized_count") or 0)
            - (right.get("invalid_or_sanitized_count") or 0),
            "unknown_field_count": (left.get("unknown_field_count") or 0)
            - (right.get("unknown_field_count") or 0),
            "low_margin_count": (left.get("low_margin_count") or 0)
            - (right.get("low_margin_count") or 0),
        },
    }


def worst_cases(db_path: Path, run_id: str, top_k: int) -> list[dict[str, object]]:
    conn = _connect(db_path)
    rows = conn.execute(
        """
        SELECT
          tick,
          latency_ms,
          fallback_used,
          invalid_or_sanitized,
          unknown_field_count,
          top_margin
        FROM replay_ticks
        WHERE run_id = ?
        ORDER BY
          CASE WHEN invalid_or_sanitized = 1 THEN 0 ELSE 1 END,
          CASE WHEN fallback_used = 1 THEN 0 ELSE 1 END,
          CASE WHEN unknown_field_count > 0 THEN 0 ELSE 1 END,
          COALESCE(top_margin, 9999.0) ASC,
          COALESCE(latency_ms, 0) DESC
        LIMIT ?
        """,
        (run_id, top_k),
    ).fetchall()
    return [
        {
            "tick": row[0],
            "latency_ms": row[1],
            "fallback_used": bool(row[2]),
            "invalid_or_sanitized": bool(row[3]),
            "unknown_field_count": row[4],
            "top_margin": row[5],
        }
        for row in rows
    ]


def export_anomalies(db_path: Path, run_id: str, output: Path, margin: float) -> Path:
    conn = _connect(db_path)
    rows = conn.execute(
        """
        SELECT
          tick,
          latency_ms,
          fallback_used,
          invalid_or_sanitized,
          unknown_field_count,
          top_margin,
          source_file
        FROM replay_ticks
        WHERE run_id = ?
          AND (
            fallback_used = 1
            OR invalid_or_sanitized = 1
            OR unknown_field_count > 0
            OR (top_margin IS NOT NULL AND top_margin <= ?)
          )
        ORDER BY tick
        """,
        (run_id, margin),
    ).fetchall()
    out = [
        {
            "tick": row[0],
            "latency_ms": row[1],
            "fallback_used": bool(row[2]),
            "invalid_or_sanitized": bool(row[3]),
            "unknown_field_count": row[4],
            "top_margin": row[5],
            "source_file": row[6],
        }
        for row in rows
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay analytics + SQLite ingestion")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest_parser = sub.add_parser("ingest")
    ingest_parser.add_argument("--replay-dir", type=Path, default=Path("logs/replay"))
    ingest_parser.add_argument("--manifest-dir", type=Path, default=Path("ops/manifests"))
    ingest_parser.add_argument("--db", type=Path, default=Path("logs/analytics/replays.sqlite"))

    summarize_parser = sub.add_parser("summarize-run")
    summarize_parser.add_argument("run_id", type=str)
    summarize_parser.add_argument("--db", type=Path, default=Path("logs/analytics/replays.sqlite"))

    compare_parser = sub.add_parser("compare-runs")
    compare_parser.add_argument("run_a", type=str)
    compare_parser.add_argument("run_b", type=str)
    compare_parser.add_argument("--db", type=Path, default=Path("logs/analytics/replays.sqlite"))

    worst_parser = sub.add_parser("worst-cases")
    worst_parser.add_argument("run_id", type=str)
    worst_parser.add_argument("--top-k", type=int, default=10)
    worst_parser.add_argument("--db", type=Path, default=Path("logs/analytics/replays.sqlite"))

    export_parser = sub.add_parser("export-anomalies")
    export_parser.add_argument("run_id", type=str)
    export_parser.add_argument("output", type=Path)
    export_parser.add_argument("--margin", type=float, default=0.05)
    export_parser.add_argument("--db", type=Path, default=Path("logs/analytics/replays.sqlite"))

    args = parser.parse_args()

    if args.command == "ingest":
        print(
            json.dumps(
                ingest(args.replay_dir, args.manifest_dir, args.db), ensure_ascii=False, indent=2
            )
        )
    elif args.command == "summarize-run":
        print(json.dumps(summarize_run(args.db, args.run_id), ensure_ascii=False, indent=2))
    elif args.command == "compare-runs":
        print(
            json.dumps(compare_runs(args.db, args.run_a, args.run_b), ensure_ascii=False, indent=2)
        )
    elif args.command == "worst-cases":
        print(
            json.dumps(worst_cases(args.db, args.run_id, args.top_k), ensure_ascii=False, indent=2)
        )
    elif args.command == "export-anomalies":
        output = export_anomalies(args.db, args.run_id, args.output, args.margin)
        print(str(output))


if __name__ == "__main__":
    main()
