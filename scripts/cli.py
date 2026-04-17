from __future__ import annotations

import argparse
import json
import os
import socket
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from datsteam_core.config.settings import FullSettings
from datsteam_core.ops import build_run_manifest, load_run_manifest, save_run_manifest
from datsteam_core.transport.http import (
    TransportError,
    TransportHttpStatusError,
    TransportNetworkError,
    TransportTimeoutError,
)
from datsteam_core.types.core import ActionSink, CanonicalState, StateProvider, TickBudget
from games.datsblack.live import DryRunActionSink, build_client, client_action_sink, load_settings
from games.datsblack.models.raw import ShipsCommands
from games.datssol.adapter import DatsSolActionSink, DatsSolStateProvider
from games.datssol.api.client import DatsSolClient
from games.datssol.canonical.state import to_canonical
from games.datssol.evaluator.features import extract_features
from games.datssol.evaluator.scorer import score_scheduled_action
from games.datssol.exit_scheduler import schedule_candidates
from games.datssol.legal_actions import generate_candidates
from games.datssol.models.raw import ArenaResponse, CommandRequest
from games.datssol.strategy.baseline import DatsSolBaselineStrategy
from games.datssol.strategy.legal import DatsSolActionValidator
from games.datssol.timeouts import DatsSolTimeoutPolicy


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Datsteam starter CLI")
    parser.add_argument("--config", type=Path, default=None, help="Optional YAML config")

    sub = parser.add_subparsers(dest="scope", required=True)

    fixture = sub.add_parser("fixture-run", help="Run offline runtime fixture loop")
    fixture.add_argument(
        "--fixture", type=Path, default=Path("tests/fixtures/datsblack_scan_multi_tick.json")
    )

    db = sub.add_parser("datsblack", help="DatsBlack live commands")
    db_sub = db.add_subparsers(dest="command", required=True)

    db_sub.add_parser("scan")
    db_sub.add_parser("map")

    reg = db_sub.add_parser("register")
    reg.add_argument("--mode", choices=["deathmatch", "royal"], required=True)

    exit_battle = db_sub.add_parser("exit")
    exit_battle.add_argument("--mode", choices=["deathmatch"], default="deathmatch")

    loop = db_sub.add_parser("loop")
    loop.add_argument("--ticks", type=int, default=1)
    loop.add_argument("--dry-run", action="store_true")
    loop.add_argument(
        "--fixture",
        type=Path,
        default=Path("tests/fixtures/datsblack_scan_multi_tick.json"),
        help="Fixture path for offline dry-run loop mode",
    )
    loop.add_argument("--manifest", type=Path, default=None)
    loop.add_argument("--policy-id", type=str, default="safe_baseline")
    loop.add_argument("--run-mode", type=str, default="training")
    loop.add_argument("--environment", type=str, default="local")

    db_sub.add_parser("dry-run")

    ds = sub.add_parser("datssol", help="DatsSol live commands")
    ds_sub = ds.add_subparsers(dest="command", required=True)
    ds_sub.add_parser("arena")
    ds_sub.add_parser("logs")
    ds_sub.add_parser("doctor")
    ds_sub.add_parser("once")
    ds_watch = ds_sub.add_parser("watch")
    ds_watch.add_argument("--ticks", type=int, default=10)
    ds_dry = ds_sub.add_parser("dry-run")
    ds_dry.add_argument(
        "--fixture",
        type=Path,
        default=Path("tests/fixtures/datssol/arena_sample.json"),
    )
    ds_submit = ds_sub.add_parser("submit")
    ds_submit.add_argument("--file", type=Path, required=True)
    ds_submit.add_argument("--dry-run", action="store_true")
    ds_cmd = ds_sub.add_parser("command")
    ds_cmd.add_argument("--from-file", type=Path, required=True)
    ds_loop = ds_sub.add_parser("loop")
    ds_loop.add_argument("--ticks", type=int, default=1)
    ds_loop.add_argument("--dry-run", action="store_true")
    ds_loop.add_argument(
        "--fixture",
        type=Path,
        default=Path("tests/fixtures/datssol/arena_sample.json"),
    )
    ds_loop.add_argument("--watch-only", action="store_true")
    ds_auto = ds_sub.add_parser("autoplay")
    ds_auto.add_argument("--hours", type=float, default=8.0)
    ds_auto.add_argument("--ticks", type=int, default=None)
    ds_auto.add_argument("--watch-only", action="store_true")
    ds_auto.add_argument("--session-name", type=str, default="autoplay")
    ds_auto.add_argument("--summary-every", type=int, default=25)
    ds_auto.add_argument("--max-consecutive-errors", type=int, default=20)

    ops = sub.add_parser("ops", help="Operational utilities")
    ops_sub = ops.add_subparsers(dest="command", required=True)

    create = ops_sub.add_parser("create-manifest", help="Create run manifest JSON")
    create.add_argument("--output", type=Path, required=True)
    create.add_argument("--policy-id", type=str, default="safe_baseline")
    create.add_argument("--mode", type=str, default="training")
    create.add_argument("--environment", type=str, default="local")

    bench = ops_sub.add_parser("benchmark", help="Measure endpoint latency")
    bench.add_argument("--url", type=str, required=True)
    bench.add_argument("--samples", type=int, default=5)
    bench.add_argument("--timeout", type=float, default=3.0)
    bench.add_argument("--auth-header", type=str, default=None)
    bench.add_argument("--auth-token", type=str, default=None)
    return parser


def _run_fixture(fixture: Path) -> int:
    from scripts.run_runtime_fixture_loop import main as fixture_main

    if not fixture.exists():
        print(json.dumps({"error": f"fixture does not exist: {fixture}"}))
        return 2
    fixture_main(fixture_path=fixture)
    return 0


def _require_auth(settings: FullSettings) -> None:
    if settings.app.auth.token in {"", "replace_me"}:
        raise SystemExit(
            "Missing auth token. Set DATASTEAM_API_KEY or use --config with auth.token"
        )


def _run_datsblack(args: argparse.Namespace, settings: FullSettings) -> int:
    if args.command == "dry-run":
        sample = ShipsCommands(ships=[])
        print(json.dumps({"dry_run": True, "validated": sample.model_dump(exclude_none=True)}))
        return 0

    if args.command == "loop":
        from datsteam_core.replay.store import ReplayWriter
        from datsteam_core.runtime.loop import RuntimeLoop
        from games.datsblack.adapter import DatsBlackStateProvider
        from games.datsblack.strategy.baseline import SafeBaselineStrategy
        from games.datsblack.strategy.legal import DatsBlackActionValidator
        from scripts.run_runtime_fixture_loop import FixtureStateProvider

        manifest = (
            load_run_manifest(args.manifest)
            if args.manifest
            else build_run_manifest(
                settings=settings,
                policy_id=args.policy_id,
                mode=args.run_mode,
                environment=args.environment,
            )
        )

        if args.dry_run:
            if not args.fixture.exists():
                print(json.dumps({"error": f"fixture does not exist: {args.fixture}"}))
                return 2
            state_provider: StateProvider = FixtureStateProvider(args.fixture)
            sink: ActionSink = DryRunActionSink()
        else:
            _require_auth(settings)
            client = build_client(settings)
            state_provider = DatsBlackStateProvider(client=client)
            sink = client_action_sink(client)

        loop = RuntimeLoop(
            state_provider=state_provider,
            strategy=SafeBaselineStrategy(),
            action_validator=DatsBlackActionValidator(),
            action_sink=sink,
            replay_writer=ReplayWriter(
                settings.app.runtime.replay_dir,
                session_id=manifest.session_id,
                run_metadata=manifest.as_replay_metadata(),
            ),
            send_margin_ms=settings.app.runtime.send_margin_ms,
        )

        outputs = [loop.step() for _ in range(args.ticks)]
        print(
            json.dumps(
                {"manifest": manifest.as_replay_metadata(), "results": outputs},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    _require_auth(settings)
    client = build_client(settings)

    if args.command == "scan":
        print(json.dumps(client.scan().model_dump(exclude_none=True), ensure_ascii=False, indent=2))
        return 0

    if args.command == "map":
        print(
            json.dumps(client.get_map().model_dump(exclude_none=True), ensure_ascii=False, indent=2)
        )
        return 0

    if args.command == "register":
        if args.mode == "deathmatch":
            payload = client.register_deathmatch().model_dump(exclude_none=True)
        else:
            payload = client.register_royal().model_dump(exclude_none=True)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "exit":
        print(
            json.dumps(
                client.exit_deathmatch().model_dump(exclude_none=True), ensure_ascii=False, indent=2
            )
        )
        return 0

    print(json.dumps({"error": f"Unsupported command: {args.command}"}))
    return 2


class _DatsSolFixtureProvider:
    def __init__(self, fixture_path: Path) -> None:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        states = payload if isinstance(payload, list) else [payload]
        self._states = [to_canonical(ArenaResponse.model_validate(item)).state for item in states]
        self._idx = 0

    def poll(self) -> CanonicalState:
        if self._idx >= len(self._states):
            state = self._states[-1]
        else:
            state = self._states[self._idx]
            self._idx += 1
        return state


class _DatsSolDryRunActionSink:
    def submit(self, action: object) -> dict[str, object]:
        payload = getattr(action, "payload", {})
        if not isinstance(payload, dict) or not payload:
            return {"code": 0, "errors": ["dry-run: skipped submit"]}
        return {"code": 0, "errors": [], "dry_run": True, "payload": payload}


def _build_datssol_client(settings: FullSettings) -> DatsSolClient:
    from datsteam_core.auth.headers import HeaderTokenAuth
    from datsteam_core.transport.http import HttpTransport, RetryPolicy

    auth_headers = HeaderTokenAuth(
        header_name=settings.app.auth.header_name,
        token=settings.app.auth.token,
    ).headers()
    transport = HttpTransport(
        base_url=settings.app.api_base_url,
        default_headers=auth_headers,
        timeout_seconds=settings.app.runtime.timeout_seconds,
        retry_policy=RetryPolicy(
            retries=settings.app.runtime.retries,
            backoff_initial_seconds=settings.app.runtime.backoff_initial_seconds,
            backoff_multiplier=settings.app.runtime.backoff_multiplier,
            backoff_max_seconds=settings.app.runtime.backoff_max_seconds,
        ),
        accept_gzip=settings.app.runtime.accept_gzip,
    )
    return DatsSolClient(
        transport=transport,
        timeout_policy=DatsSolTimeoutPolicy(
            base_timeout_seconds=settings.app.runtime.timeout_seconds,
            send_margin_ms=settings.app.runtime.send_margin_ms,
            hot_timeout_seconds=settings.app.runtime.hot_timeout_seconds,
            cold_timeout_seconds=settings.app.runtime.cold_timeout_seconds,
            arena_timeout_seconds=settings.app.runtime.arena_timeout_seconds,
            command_timeout_seconds=settings.app.runtime.command_timeout_seconds,
            logs_timeout_seconds=settings.app.runtime.logs_timeout_seconds,
        ),
    )


def _datssol_live_dir() -> Path:
    return Path("logs/live")


def _datssol_sessions_dir() -> Path:
    return _datssol_live_dir() / "sessions"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_ndjson(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _slugify_session_name(value: str | None) -> str:
    if not isinstance(value, str):
        return "autoplay"
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    cleaned = cleaned.strip("_")
    return cleaned or "autoplay"


def _create_datssol_session_dir(session_name: str | None) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    path = _datssol_sessions_dir() / f"{stamp}_{_slugify_session_name(session_name)}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _increment_counter(counters: dict[str, int], key: str) -> None:
    counters[key] = counters.get(key, 0) + 1


def _recommended_turn_sleep_seconds(
    *,
    next_turn_in: object,
    cycle_latency_ms: object,
    post_turn_buffer_seconds: float = 0.02,
    min_sleep_seconds: float = 0.05,
) -> float | None:
    if not isinstance(next_turn_in, (int, float)):
        return None
    latency_seconds = 0.0
    if isinstance(cycle_latency_ms, (int, float)):
        latency_seconds = max(0.0, float(cycle_latency_ms) / 1000.0)
    remaining = float(next_turn_in) - latency_seconds + post_turn_buffer_seconds
    return max(min_sleep_seconds, remaining)


def _new_session_summary(
    *,
    session_dir: Path,
    session_name: str,
    do_submit: bool,
    target_ticks: int | None,
    target_hours: float | None,
) -> dict[str, object]:
    return {
        "session_dir": str(session_dir),
        "session_name": session_name,
        "pid": os.getpid(),
        "started_at": datetime.now(UTC).isoformat(),
        "ended_at": None,
        "do_submit": do_submit,
        "target_ticks": target_ticks,
        "target_hours": target_hours,
        "cycles_total": 0,
        "unique_turns": 0,
        "duplicate_turns": 0,
        "idle_cycles": 0,
        "fallback_count": 0,
        "submit_attempts": 0,
        "submit_successes": 0,
        "submit_failures": 0,
        "error_events": 0,
        "rate_limit_events": 0,
        "network_events": 0,
        "timeout_events": 0,
        "transport_events": 0,
        "action_breakdown": {},
        "submit_skip_reasons": {},
        "error_codes": {},
        "avg_next_turn_in": 0.0,
        "avg_latency_ms": 0.0,
        "max_plantation_count": 0,
        "max_isolated_count": 0,
        "max_critical_bridge_count": 0,
        "max_construction_count": 0,
        "low_confidence_turns": 0,
        "last_turn": None,
        "last_timestamp": None,
        "last_main_position": None,
        "last_main_hp": None,
        "last_main_ttf": None,
        "_sum_next_turn_in": 0.0,
        "_sum_latency_ms": 0.0,
    }


def _update_session_summary(summary: dict[str, object], cycle: dict[str, object]) -> None:
    cycles_total = int(summary.get("cycles_total", 0)) + 1
    summary["cycles_total"] = cycles_total
    if bool(cycle.get("duplicate_turn_seen")):
        summary["duplicate_turns"] = int(summary.get("duplicate_turns", 0)) + 1
    else:
        summary["unique_turns"] = int(summary.get("unique_turns", 0)) + 1
    if bool(cycle.get("idle")):
        summary["idle_cycles"] = int(summary.get("idle_cycles", 0)) + 1
    if bool(cycle.get("fallback_used")):
        summary["fallback_count"] = int(summary.get("fallback_count", 0)) + 1
    if bool(cycle.get("submit_attempted")):
        summary["submit_attempts"] = int(summary.get("submit_attempts", 0)) + 1

    next_turn_in = cycle.get("nextTurnIn")
    if isinstance(next_turn_in, (int, float)):
        total = float(summary.get("_sum_next_turn_in", 0.0)) + float(next_turn_in)
        summary["_sum_next_turn_in"] = total
        summary["avg_next_turn_in"] = round(total / cycles_total, 4)

    latency_ms = cycle.get("latency_ms")
    if isinstance(latency_ms, (int, float)):
        total = float(summary.get("_sum_latency_ms", 0.0)) + float(latency_ms)
        summary["_sum_latency_ms"] = total
        summary["avg_latency_ms"] = round(total / cycles_total, 2)

    summary["max_plantation_count"] = max(
        int(summary.get("max_plantation_count", 0)),
        _safe_int(cycle.get("plantation_count"), default=0),
    )
    summary["max_isolated_count"] = max(
        int(summary.get("max_isolated_count", 0)),
        _safe_int(cycle.get("isolated_count"), default=0),
    )
    summary["max_critical_bridge_count"] = max(
        int(summary.get("max_critical_bridge_count", 0)),
        _safe_int(cycle.get("critical_bridge_count"), default=0),
    )
    summary["max_construction_count"] = max(
        int(summary.get("max_construction_count", 0)),
        _safe_int(cycle.get("construction_count"), default=0),
    )

    action = cycle.get("action")
    action_breakdown = summary.get("action_breakdown")
    if not isinstance(action_breakdown, dict):
        action_breakdown = {}
        summary["action_breakdown"] = action_breakdown
    if isinstance(action, dict):
        if isinstance(action.get("command"), list):
            _increment_counter(action_breakdown, "command")
        if isinstance(action.get("relocateMain"), list):
            _increment_counter(action_breakdown, "relocateMain")
        if isinstance(action.get("plantationUpgrade"), str):
            _increment_counter(action_breakdown, "plantationUpgrade")
        if not action:
            _increment_counter(action_breakdown, "hold")

    skip_reasons = summary.get("submit_skip_reasons")
    if not isinstance(skip_reasons, dict):
        skip_reasons = {}
        summary["submit_skip_reasons"] = skip_reasons
    reason = cycle.get("submit_skipped_reason")
    if isinstance(reason, str) and reason:
        _increment_counter(skip_reasons, reason)

    result = cycle.get("result")
    if isinstance(result, dict):
        code = result.get("code")
        if isinstance(code, int):
            codes = summary.get("error_codes")
            if not isinstance(codes, dict):
                codes = {}
                summary["error_codes"] = codes
            _increment_counter(codes, str(code))
            if code == 0 and not result.get("errors"):
                summary["submit_successes"] = int(summary.get("submit_successes", 0)) + 1
            else:
                summary["submit_failures"] = int(summary.get("submit_failures", 0)) + 1

    summary["last_turn"] = cycle.get("turnNo")
    summary["last_timestamp"] = cycle.get("timestamp")
    summary["last_main_position"] = cycle.get("main_position")
    summary["last_main_hp"] = cycle.get("main_hp")
    summary["last_main_ttf"] = cycle.get("main_ttf")
    choice_margin = cycle.get("choice_margin")
    if isinstance(choice_margin, (int, float)) and float(choice_margin) < 0.5:
        summary["low_confidence_turns"] = int(summary.get("low_confidence_turns", 0)) + 1


def _record_session_event(
    session_dir: Path,
    *,
    kind: str,
    payload: dict[str, object],
) -> None:
    event = {"timestamp": datetime.now(UTC).isoformat(), "kind": kind, **payload}
    _append_ndjson(session_dir / "events.ndjson", event)


def _update_session_errors(summary: dict[str, object], exc: TransportError) -> None:
    summary["error_events"] = int(summary.get("error_events", 0)) + 1
    summary["transport_events"] = int(summary.get("transport_events", 0)) + 1
    if isinstance(exc, TransportHttpStatusError) and exc.status_code == 429:
        summary["rate_limit_events"] = int(summary.get("rate_limit_events", 0)) + 1
    elif isinstance(exc, TransportTimeoutError):
        summary["timeout_events"] = int(summary.get("timeout_events", 0)) + 1
    elif isinstance(exc, TransportNetworkError):
        summary["network_events"] = int(summary.get("network_events", 0)) + 1


def _transport_backoff_seconds(exc: TransportError, consecutive_errors: int) -> float:
    if isinstance(exc, TransportHttpStatusError) and exc.status_code == 429:
        return min(2.0, 0.35 * (2 ** max(0, consecutive_errors - 1)))
    if isinstance(exc, TransportTimeoutError):
        return min(4.0, 0.5 * (2 ** max(0, consecutive_errors - 1)))
    if isinstance(exc, TransportNetworkError):
        return min(4.0, 0.5 * (2 ** max(0, consecutive_errors - 1)))
    return min(4.0, 0.5 * (2 ** max(0, consecutive_errors - 1)))


def _is_datssol_idle(arena: ArenaResponse) -> bool:
    if arena.size == [0, 0]:
        return True
    if len(arena.plantations) == 0:
        return True
    return False


def _doctor_payload(settings: FullSettings) -> dict[str, object]:
    runtime = settings.app.runtime
    token_loaded = settings.app.auth.token not in {"", "replace_me"}
    return {
        "game": settings.app.game,
        "token_loaded": token_loaded,
        "base_url": settings.app.api_base_url,
        "auth_header": settings.app.auth.header_name,
        "replay_dir": str(runtime.replay_dir),
        "timeouts": {
            "global_timeout_seconds": runtime.timeout_seconds,
            "send_margin_ms": runtime.send_margin_ms,
            "hot_timeout_seconds": runtime.hot_timeout_seconds,
            "cold_timeout_seconds": runtime.cold_timeout_seconds,
            "arena_timeout_seconds": runtime.arena_timeout_seconds,
            "command_timeout_seconds": runtime.command_timeout_seconds,
            "logs_timeout_seconds": runtime.logs_timeout_seconds,
        },
    }


def _point_from_raw(raw: object) -> tuple[int, int] | None:
    if isinstance(raw, list) and len(raw) == 2 and all(isinstance(v, int) for v in raw):
        return (raw[0], raw[1])
    return None


def _safe_int(value: object, *, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return default


def _path_to_lists(path: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]) -> list[list[int]]:
    return [list(path[0]), list(path[1]), list(path[2])]


def _estimate_ttf(progress: object) -> int | None:
    if not isinstance(progress, int):
        return None
    remaining = max(0, 100 - progress)
    return max(0, (remaining + 9) // 10)


def _beaver_threat(point: tuple[int, int] | None, beavers: object) -> int:
    if point is None or not isinstance(beavers, list):
        return 0
    total = 0
    for item in beavers:
        if not isinstance(item, dict):
            continue
        pos = _point_from_raw(item.get("position"))
        if pos is None:
            continue
        if abs(point[0] - pos[0]) <= 2 and abs(point[1] - pos[1]) <= 2:
            total += 1
    return total


def _run_datssol_cycle(
    *,
    client: DatsSolClient,
    do_submit: bool,
    submitted_turns: set[int],
    session_dir: Path | None = None,
) -> dict[str, object]:
    started = time.perf_counter()
    arena = client.arena()
    arena_payload = arena.model_dump(exclude_none=True)
    _write_json(_datssol_live_dir() / "latest_arena.json", arena_payload)
    if session_dir is not None:
        _write_json(session_dir / "latest_arena.json", arena_payload)
        _append_ndjson(session_dir / "arena.ndjson", arena_payload)

    state = to_canonical(arena).state
    summary: dict[str, object] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "turnNo": arena.turnNo,
        "nextTurnIn": float(arena.nextTurnIn),
        "idle": _is_datssol_idle(arena),
        "submit_attempted": False,
        "submit_skipped_reason": None,
        "action": {},
        "result": None,
        "errors": [],
        "fallback_used": False,
        "main_position": None,
        "main_hp": None,
        "main_progress": None,
        "main_ttf": None,
        "plantation_count": len(arena.plantations),
        "isolated_count": 0,
        "critical_bridge_count": 0,
        "construction_count": len(arena.construction),
        "construction_progress": [],
        "main_beaver_threat": 0,
        "bridge_beaver_threats": [],
        "meteoForecasts": state.metadata.get("meteo_forecasts", []),
        "exit_usage": {},
        "decision_reason": None,
        "candidate_count": 0,
        "candidate_shortlist": [],
        "choice_margin": None,
        "main_under_threat": False,
    }

    plantations = state.metadata.get("plantations")
    main_point: tuple[int, int] | None = None
    if isinstance(plantations, dict):
        isolated_count = 0
        for item in plantations.values():
            if not isinstance(item, dict):
                continue
            if bool(item.get("is_isolated")):
                isolated_count += 1
            if bool(item.get("is_main")):
                summary["main_position"] = item.get("position")
                summary["main_hp"] = item.get("hp")
                main_point = _point_from_raw(item.get("position"))
        summary["isolated_count"] = isolated_count

    cells = state.metadata.get("cells")
    if isinstance(cells, list) and main_point is not None:
        for item in cells:
            if not isinstance(item, dict):
                continue
            pos = _point_from_raw(item.get("position"))
            if pos != main_point:
                continue
            progress = item.get("terraformationProgress")
            summary["main_progress"] = progress
            summary["main_ttf"] = _estimate_ttf(progress)
            break

    critical_bridges = state.metadata.get("critical_bridges")
    if isinstance(critical_bridges, list):
        summary["critical_bridge_count"] = len(critical_bridges)
        summary["bridge_beaver_threats"] = [
            {
                "position": point,
                "beaver_threat": _beaver_threat(_point_from_raw(point), state.metadata.get("beavers")),
            }
            for point in critical_bridges
        ]

    construction = state.metadata.get("construction")
    if isinstance(construction, list):
        summary["construction_progress"] = [
            {
                "position": item.get("position"),
                "progress": item.get("progress"),
            }
            for item in construction
            if isinstance(item, dict)
        ]

    summary["main_beaver_threat"] = _beaver_threat(main_point, state.metadata.get("beavers"))
    forecasts = state.metadata.get("meteo_forecasts")
    earthquake_turns_until = None
    if isinstance(forecasts, list):
        values = [
            item.get("turnsUntil")
            for item in forecasts
            if isinstance(item, dict) and item.get("kind") == "earthquake"
        ]
        earthquakes = [value for value in values if isinstance(value, int)]
        if earthquakes:
            earthquake_turns_until = min(earthquakes)
    summary["main_under_threat"] = bool(
        (
            isinstance(summary.get("main_hp"), int)
            and int(summary["main_hp"]) <= 26
        )
        or int(summary["main_beaver_threat"]) > 0
        or (isinstance(earthquake_turns_until, int) and earthquake_turns_until <= 1)
    )

    if summary["idle"]:
        summary["submit_skipped_reason"] = "idle_arena"
    else:
        candidates = generate_candidates(state)
        summary["candidate_count"] = len(candidates)
        features = extract_features(state)
        scored_candidates: list[dict[str, object]] = []
        for item in schedule_candidates(candidates, limit=5):
            breakdown = score_scheduled_action(item, features)
            scored_candidates.append(
                {
                    "path": _path_to_lists(item.candidate.path),
                    "base_score": round(item.candidate.base_score, 3),
                    "adjusted_score": round(item.adjusted_score, 3),
                    "exit_use_index": item.exit_use_index,
                    "total": round(breakdown.total, 3),
                    "components": {key: round(value, 3) for key, value in breakdown.components.items()},
                }
            )
        scored_candidates.sort(key=lambda item: float(item["total"]), reverse=True)
        summary["candidate_shortlist"] = scored_candidates
        if len(scored_candidates) >= 2:
            summary["choice_margin"] = round(
                float(scored_candidates[0]["total"]) - float(scored_candidates[1]["total"]),
                3,
            )
        elif scored_candidates:
            summary["choice_margin"] = float(scored_candidates[0]["total"])

        strategy = DatsSolBaselineStrategy()
        proposed = strategy.choose_action(state, budget=TickBudget(tick=state.tick))
        cleaned = DatsSolActionValidator().sanitize(proposed, state)
        summary["action"] = cleaned.payload
        summary["decision_reason"] = proposed.reason
        summary["fallback_used"] = "fallback_" in proposed.reason
        exit_usage: dict[str, int] = {}
        commands = cleaned.payload.get("command")
        if isinstance(commands, list):
            for item in commands:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                if not isinstance(path, list) or len(path) < 2:
                    continue
                exit_point = path[1]
                if not (isinstance(exit_point, list) and len(exit_point) == 2):
                    continue
                key = f"{exit_point[0]},{exit_point[1]}"
                exit_usage[key] = exit_usage.get(key, 0) + 1
        summary["exit_usage"] = exit_usage

        request = CommandRequest.model_validate(cleaned.payload)
        if not request.has_useful_action():
            summary["submit_skipped_reason"] = "empty_payload_prevented"
        elif arena.turnNo in submitted_turns:
            summary["submit_skipped_reason"] = "duplicate_turn_guard"
        elif do_submit:
            summary["submit_attempted"] = True
            outcome = client.submit_command(
                request,
                next_turn_in_seconds=float(arena.nextTurnIn),
            )
            submitted_turns.add(arena.turnNo)
            summary["result"] = outcome.response.model_dump(exclude_none=True)
            if isinstance(summary["result"], dict):
                summary["errors"] = list(summary["result"].get("errors", []))
                if session_dir is not None:
                    _write_json(session_dir / "latest_result.json", summary["result"])
        else:
            summary["submit_skipped_reason"] = "watch_mode"

    latency_ms = int((time.perf_counter() - started) * 1000)
    summary["latency_ms"] = latency_ms
    _append_ndjson(_datssol_live_dir() / "command_history.ndjson", summary)
    if isinstance(summary["errors"], list) and summary["errors"]:
        _append_ndjson(_datssol_live_dir() / "errors.ndjson", summary)
    return summary


def _run_datssol_session(
    *,
    client: DatsSolClient,
    do_submit: bool,
    ticks: int | None,
    hours: float | None,
    session_name: str,
    summary_every: int,
    max_consecutive_errors: int,
) -> dict[str, object]:
    session_dir = _create_datssol_session_dir(session_name)
    summary = _new_session_summary(
        session_dir=session_dir,
        session_name=session_name,
        do_submit=do_submit,
        target_ticks=ticks,
        target_hours=hours,
    )
    _write_json(session_dir / "summary.json", summary)
    _write_json(
        session_dir / "manifest.json",
        {
            "session_name": session_name,
            "pid": os.getpid(),
            "do_submit": do_submit,
            "ticks": ticks,
            "hours": hours,
            "started_at": summary["started_at"],
        },
    )
    _write_json(
        _datssol_live_dir() / "active_session.json",
        {
            "session_dir": str(session_dir),
            "session_name": session_name,
            "pid": os.getpid(),
            "started_at": summary["started_at"],
            "do_submit": do_submit,
            "ticks": ticks,
            "hours": hours,
        },
    )

    submitted_turns: set[int] = set()
    last_turn: int | None = None
    cycles_done = 0
    consecutive_errors = 0
    deadline = time.monotonic() + (hours * 3600.0) if hours is not None else None

    while True:
        if ticks is not None and cycles_done >= ticks:
            break
        if deadline is not None and time.monotonic() >= deadline:
            break
        try:
            cycle = _run_datssol_cycle(
                client=client,
                do_submit=do_submit,
                submitted_turns=submitted_turns,
                session_dir=session_dir,
            )
            turn_no = cycle.get("turnNo")
            cycle["duplicate_turn_seen"] = isinstance(turn_no, int) and turn_no == last_turn
            if isinstance(turn_no, int):
                last_turn = turn_no
            _append_ndjson(session_dir / "turns.ndjson", cycle)
            _write_json(session_dir / "latest_cycle.json", cycle)
            _update_session_summary(summary, cycle)
            consecutive_errors = 0
            cycles_done += 1

            if cycles_done == 1 or cycles_done % max(1, summary_every) == 0:
                _record_session_event(
                    session_dir,
                    kind="progress",
                    payload={
                        "cycles_total": summary["cycles_total"],
                        "last_turn": summary["last_turn"],
                        "submit_successes": summary["submit_successes"],
                        "submit_failures": summary["submit_failures"],
                    },
                )
            _write_json(session_dir / "summary.json", summary)

            if ticks is not None and cycles_done >= ticks:
                break
            if deadline is not None and time.monotonic() >= deadline:
                break

            sleep_seconds = _recommended_turn_sleep_seconds(
                next_turn_in=cycle.get("nextTurnIn"),
                cycle_latency_ms=cycle.get("latency_ms"),
            )
            if sleep_seconds is not None:
                time.sleep(sleep_seconds)
        except TransportError as exc:
            consecutive_errors += 1
            _update_session_errors(summary, exc)
            backoff_seconds = _transport_backoff_seconds(exc, consecutive_errors)
            _record_session_event(
                session_dir,
                kind="transport_error",
                payload={
                    "message": str(exc),
                    "method": exc.method,
                    "path": exc.path,
                    "attempt": exc.attempt,
                    "backoff_seconds": backoff_seconds,
                    "consecutive_errors": consecutive_errors,
                    "status_code": exc.status_code if isinstance(exc, TransportHttpStatusError) else None,
                },
            )
            _write_json(session_dir / "summary.json", summary)
            if consecutive_errors >= max(1, max_consecutive_errors):
                summary["ended_at"] = datetime.now(UTC).isoformat()
                summary["stopped_reason"] = "max_consecutive_errors"
                _write_json(session_dir / "summary.json", summary)
                return summary
            time.sleep(backoff_seconds)

    summary["ended_at"] = datetime.now(UTC).isoformat()
    summary["stopped_reason"] = "tick_limit" if ticks is not None and cycles_done >= ticks else "time_limit"
    _write_json(session_dir / "summary.json", summary)
    return summary


def _run_datssol(args: argparse.Namespace, settings: FullSettings) -> int:
    if args.command == "dry-run":
        if not args.fixture.exists():
            print(json.dumps({"error": f"fixture does not exist: {args.fixture}"}))
            return 2
        payload = json.loads(args.fixture.read_text(encoding="utf-8"))
        arena = ArenaResponse.model_validate(payload[0] if isinstance(payload, list) else payload)
        state = to_canonical(arena).state
        strategy = DatsSolBaselineStrategy()
        action = DatsSolActionValidator().sanitize(
            strategy.choose_action(state, budget=TickBudget(tick=state.tick)),
            state,
        )
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "turn": state.tick,
                    "action": action.payload,
                    "reason": action.reason,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "doctor":
        print(json.dumps(_doctor_payload(settings), ensure_ascii=False, indent=2))
        return 0

    if args.command == "submit" and args.dry_run:
        body = json.loads(args.file.read_text(encoding="utf-8"))
        payload = CommandRequest.model_validate(body)
        print(
            json.dumps(
                {"dry_run": True, "payload": payload.model_dump(exclude_none=True)},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "loop" and args.dry_run:
        client: DatsSolClient | None = None
    else:
        _require_auth(settings)
        client = _build_datssol_client(settings)

    if args.command == "arena":
        assert client is not None
        print(
            json.dumps(
                client.arena().model_dump(exclude_none=True), ensure_ascii=False, indent=2
            )
        )
        return 0

    if args.command == "logs":
        assert client is not None
        payload = client.logs().model_dump(exclude_none=True)
        _write_json(_datssol_live_dir() / "latest_logs.json", payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if args.command == "submit":
        body = json.loads(args.file.read_text(encoding="utf-8"))
        payload = CommandRequest.model_validate(body)
        assert client is not None
        result = client.submit_command(
            payload,
            next_turn_in_seconds=client.last_next_turn_in_seconds,
        )
        out = result.response.model_dump(exclude_none=True)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.command == "command":
        assert client is not None
        body = json.loads(args.from_file.read_text(encoding="utf-8"))
        payload = CommandRequest.model_validate(body)
        print(
            json.dumps(
                client.command(
                    payload, next_turn_in_seconds=client.last_next_turn_in_seconds
                ).model_dump(exclude_none=True),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.command == "once":
        assert client is not None
        summary = _run_datssol_cycle(client=client, do_submit=True, submitted_turns=set())
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if args.command == "watch":
        assert client is not None
        submitted_turns: set[int] = set()
        outputs = []
        total_ticks = max(args.ticks, 1)
        for idx in range(total_ticks):
            cycle = _run_datssol_cycle(
                client=client,
                do_submit=False,
                submitted_turns=submitted_turns,
            )
            outputs.append(cycle)
            if idx + 1 >= total_ticks:
                continue
            sleep_seconds = _recommended_turn_sleep_seconds(
                next_turn_in=cycle.get("nextTurnIn"),
                cycle_latency_ms=cycle.get("latency_ms"),
            )
            if sleep_seconds is not None:
                time.sleep(sleep_seconds)
        print(json.dumps({"results": outputs}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "loop":
        from datsteam_core.replay.store import ReplayWriter
        from datsteam_core.runtime.loop import RuntimeLoop

        if args.dry_run:
            if not args.fixture.exists():
                print(json.dumps({"error": f"fixture does not exist: {args.fixture}"}))
                return 2
            state_provider: StateProvider = _DatsSolFixtureProvider(args.fixture)
            sink: ActionSink = _DatsSolDryRunActionSink()
        else:
            assert client is not None
            state_provider = DatsSolStateProvider(client=client)
            sink = DatsSolActionSink(client=client)
        loop = RuntimeLoop(
            state_provider=state_provider,
            strategy=DatsSolBaselineStrategy(),
            action_validator=DatsSolActionValidator(),
            action_sink=sink,
            replay_writer=ReplayWriter(settings.app.runtime.replay_dir),
            send_margin_ms=settings.app.runtime.send_margin_ms,
        )
        if args.watch_only:
            if client is None:
                print(
                    json.dumps(
                        {"error": "--watch-only requires live client (without --dry-run)"},
                        ensure_ascii=False,
                    )
                )
                return 2
            summary = _run_datssol_session(
                client=client,
                do_submit=False,
                ticks=max(args.ticks, 1),
                hours=None,
                session_name="loop_watch",
                summary_every=max(5, min(max(args.ticks, 1), 25)),
                max_consecutive_errors=10,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

        if not args.dry_run:
            assert client is not None
            summary = _run_datssol_session(
                client=client,
                do_submit=True,
                ticks=max(args.ticks, 1),
                hours=None,
                session_name="loop_submit",
                summary_every=max(5, min(max(args.ticks, 1), 25)),
                max_consecutive_errors=10,
            )
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 0

        outputs = [loop.step() for _ in range(args.ticks)]
        print(json.dumps({"results": outputs}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "autoplay":
        assert client is not None
        summary = _run_datssol_session(
            client=client,
            do_submit=not args.watch_only,
            ticks=args.ticks,
            hours=max(0.01, float(args.hours)),
            session_name=args.session_name,
            summary_every=max(1, args.summary_every),
            max_consecutive_errors=max(1, args.max_consecutive_errors),
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    return 2


def _measure_connect_ms(url: str, timeout: float) -> int | None:
    parsed = urlparse(url)
    if not parsed.hostname:
        return None
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    start = time.perf_counter()
    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout):
            pass
    except OSError:
        return None
    return int((time.perf_counter() - start) * 1000)


def _run_ops(args: argparse.Namespace, settings: FullSettings) -> int:
    if args.command == "create-manifest":
        manifest = build_run_manifest(
            settings=settings,
            policy_id=args.policy_id,
            mode=args.mode,
            environment=args.environment,
        )
        save_run_manifest(manifest, args.output)
        print(json.dumps(manifest.as_replay_metadata(), ensure_ascii=False, indent=2))
        return 0

    if args.command == "benchmark":
        import httpx

        headers: dict[str, str] = {}
        header_name = args.auth_header or settings.app.auth.header_name
        token = args.auth_token or settings.app.auth.token
        if token not in {"", "replace_me"}:
            headers[header_name] = token

        connect_samples: list[int] = []
        total_samples: list[int] = []
        read_samples: list[int] = []
        failures = 0

        with httpx.Client(timeout=args.timeout) as client:
            for _ in range(max(args.samples, 1)):
                connect_ms = _measure_connect_ms(args.url, args.timeout)
                if connect_ms is not None:
                    connect_samples.append(connect_ms)
                start = time.perf_counter()
                try:
                    client.get(args.url, headers=headers)
                except httpx.HTTPError:
                    failures += 1
                    continue
                total_ms = int((time.perf_counter() - start) * 1000)
                total_samples.append(total_ms)
                if connect_ms is not None:
                    read_samples.append(max(total_ms - connect_ms, 0))

        payload: dict[str, object] = {
            "url": args.url,
            "samples": args.samples,
            "failures": failures,
            "connect_ms_avg": int(sum(connect_samples) / len(connect_samples))
            if connect_samples
            else None,
            "read_ms_avg": int(sum(read_samples) / len(read_samples)) if read_samples else None,
            "total_ms_avg": int(sum(total_samples) / len(total_samples)) if total_samples else None,
        }
        if payload["total_ms_avg"] is not None:
            total_raw = payload["total_ms_avg"]
            if isinstance(total_raw, int):
                total = total_raw
            elif isinstance(total_raw, float | str):
                total = int(total_raw)
            else:
                total = 50
            payload["recommended_send_margin_ms"] = max(50, total * 2)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    return 2


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    settings = load_settings(args.config)

    if args.scope == "fixture-run":
        return _run_fixture(args.fixture)
    if args.scope == "datsblack":
        return _run_datsblack(args, settings)
    if args.scope == "datssol":
        return _run_datssol(args, settings)
    if args.scope == "ops":
        return _run_ops(args, settings)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
