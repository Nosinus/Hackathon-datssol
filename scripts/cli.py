from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path
from urllib.parse import urlparse

from datsteam_core.config.settings import FullSettings
from datsteam_core.ops import build_run_manifest, load_run_manifest, save_run_manifest
from games.datsblack.live import DryRunActionSink, build_client, client_action_sink, load_settings
from games.datsblack.models.raw import ShipsCommands


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
        from datsteam_core.types.core import ActionSink
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
            state_provider = FixtureStateProvider(args.fixture)
            sink = DryRunActionSink()
        else:
            _require_auth(settings)
            client = build_client(settings)
            state_provider = DatsBlackStateProvider(client=client)
            sink = client_action_sink(client)

        sink_typed: ActionSink = sink
        loop = RuntimeLoop(
            state_provider=state_provider,
            strategy=SafeBaselineStrategy(),
            action_validator=DatsBlackActionValidator(),
            action_sink=sink_typed,
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
            total = int(payload["total_ms_avg"])
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
    if args.scope == "ops":
        return _run_ops(args, settings)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
