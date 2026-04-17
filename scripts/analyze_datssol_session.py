from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Summarize a DatsSol autoplay session")
    parser.add_argument("--session-dir", type=Path, default=None)
    return parser


def _latest_session_dir(base_dir: Path) -> Path:
    sessions = sorted((base_dir / "logs" / "live" / "sessions").glob("*"))
    if not sessions:
        raise SystemExit("No session directories found under logs/live/sessions")
    return sessions[-1]


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_ndjson(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _safe_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _main() -> int:
    args = _parser().parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    session_dir = args.session_dir or _latest_session_dir(repo_root)
    session_dir = session_dir.resolve()

    summary = _load_json(session_dir / "summary.json")
    turns = _load_ndjson(session_dir / "turns.ndjson")
    events = _load_ndjson(session_dir / "events.ndjson")

    reasons = Counter()
    skip_reasons = Counter()
    submit_errors = Counter()
    targets = Counter()
    candidate_counts: list[int] = []
    choice_margins: list[float] = []
    main_hp_values: list[int] = []
    main_ttf_values: list[int] = []
    under_threat_turns = 0

    for turn in turns:
        reason = turn.get("decision_reason")
        if isinstance(reason, str) and reason:
            reasons[reason] += 1
        skip_reason = turn.get("submit_skipped_reason")
        if isinstance(skip_reason, str) and skip_reason:
            skip_reasons[skip_reason] += 1
        errors = turn.get("errors")
        if isinstance(errors, list):
            for item in errors:
                if isinstance(item, str) and item:
                    submit_errors[item] += 1

        action = turn.get("action")
        if isinstance(action, dict):
            commands = action.get("command")
            if isinstance(commands, list) and commands:
                first = commands[0]
                if isinstance(first, dict):
                    path = first.get("path")
                    if isinstance(path, list) and len(path) >= 3:
                        target = path[2]
                        if isinstance(target, list) and len(target) == 2:
                            targets[f"{target[0]},{target[1]}"] += 1

        candidate_count = turn.get("candidate_count")
        if isinstance(candidate_count, int):
            candidate_counts.append(candidate_count)
        choice_margin = _safe_float(turn.get("choice_margin"))
        if choice_margin is not None:
            choice_margins.append(choice_margin)
        main_hp = turn.get("main_hp")
        if isinstance(main_hp, int):
            main_hp_values.append(main_hp)
        main_ttf = turn.get("main_ttf")
        if isinstance(main_ttf, int):
            main_ttf_values.append(main_ttf)
        if bool(turn.get("main_under_threat")):
            under_threat_turns += 1

    report = {
        "session_dir": str(session_dir),
        "started_at": summary.get("started_at"),
        "ended_at": summary.get("ended_at"),
        "cycles_total": summary.get("cycles_total"),
        "unique_turns": summary.get("unique_turns"),
        "duplicate_turns": summary.get("duplicate_turns"),
        "submit_attempts": summary.get("submit_attempts"),
        "submit_successes": summary.get("submit_successes"),
        "submit_failures": summary.get("submit_failures"),
        "error_events": summary.get("error_events"),
        "avg_latency_ms": summary.get("avg_latency_ms"),
        "avg_next_turn_in": summary.get("avg_next_turn_in"),
        "avg_candidate_count": round(sum(candidate_counts) / len(candidate_counts), 2)
        if candidate_counts
        else None,
        "avg_choice_margin": round(sum(choice_margins) / len(choice_margins), 3)
        if choice_margins
        else None,
        "min_main_hp": min(main_hp_values) if main_hp_values else None,
        "min_main_ttf": min(main_ttf_values) if main_ttf_values else None,
        "main_under_threat_turns": under_threat_turns,
        "top_decision_reasons": reasons.most_common(8),
        "top_skip_reasons": skip_reasons.most_common(8),
        "top_submit_errors": submit_errors.most_common(8),
        "top_targets": targets.most_common(8),
        "event_kinds": Counter(
            item.get("kind") for item in events if isinstance(item.get("kind"), str)
        ).most_common(8),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
