from __future__ import annotations

import argparse
import json
import socket
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

from datsteam_core.config.settings import FullSettings
from datsteam_core.ops import build_run_manifest, load_run_manifest, save_run_manifest
from datsteam_core.types.core import ActionSink, CanonicalState, StateProvider, TickBudget
from games.datsblack.live import DryRunActionSink, build_client, client_action_sink, load_settings
from games.datsblack.models.raw import ShipsCommands
from games.datssol.adapter import DatsSolActionSink, DatsSolStateProvider
from games.datssol.api.client import DatsSolClient
from games.datssol.canonical.state import to_canonical
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


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_ndjson(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


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


def _run_datssol_cycle(
    *,
    client: DatsSolClient,
    do_submit: bool,
    submitted_turns: set[int],
) -> dict[str, object]:
    started = time.perf_counter()
    arena = client.arena()
    arena_payload = arena.model_dump(exclude_none=True)
    _write_json(_datssol_live_dir() / "latest_arena.json", arena_payload)

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
        "isolated_count": 0,
    }

    plantations = state.metadata.get("plantations")
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
        summary["isolated_count"] = isolated_count

    if summary["idle"]:
        summary["submit_skipped_reason"] = "idle_arena"
    else:
        strategy = DatsSolBaselineStrategy()
        proposed = strategy.choose_action(state, budget=TickBudget(tick=state.tick))
        cleaned = DatsSolActionValidator().sanitize(proposed, state)
        summary["action"] = cleaned.payload
        summary["fallback_used"] = "fallback_" in proposed.reason

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
        else:
            summary["submit_skipped_reason"] = "watch_mode"

    latency_ms = int((time.perf_counter() - started) * 1000)
    summary["latency_ms"] = latency_ms
    _append_ndjson(_datssol_live_dir() / "command_history.ndjson", summary)
    if isinstance(summary["errors"], list) and summary["errors"]:
        _append_ndjson(_datssol_live_dir() / "errors.ndjson", summary)
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
        if args.dry_run:
            print(
                json.dumps(
                    {"dry_run": True, "payload": payload.model_dump(exclude_none=True)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
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
        for _ in range(max(args.ticks, 1)):
            cycle = _run_datssol_cycle(
                client=client,
                do_submit=False,
                submitted_turns=submitted_turns,
            )
            outputs.append(cycle)
            next_turn = cycle.get("nextTurnIn")
            if isinstance(next_turn, int | float):
                time.sleep(max(0.05, float(next_turn)))
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
            submitted_turns = set()
            outputs = [
                _run_datssol_cycle(client=client, do_submit=False, submitted_turns=submitted_turns)
                for _ in range(args.ticks)
            ]
            print(json.dumps({"results": outputs}, ensure_ascii=False, indent=2))
            return 0

        outputs = [loop.step() for _ in range(args.ticks)]
        print(json.dumps({"results": outputs}, ensure_ascii=False, indent=2))
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
