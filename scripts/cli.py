from __future__ import annotations

import argparse
import json
from pathlib import Path

from datsteam_core.config.settings import FullSettings
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

    db_sub.add_parser("dry-run")
    return parser


def _run_fixture(fixture: Path) -> int:
    from scripts.run_runtime_fixture_loop import main as fixture_main

    if not fixture.exists():
        print(json.dumps({"error": f"fixture does not exist: {fixture}"}))
        return 2
    fixture_main()
    return 0


def _require_auth(settings: FullSettings) -> None:
    if settings.app.auth.token in {"", "replace_me"}:
        raise SystemExit(
            "Missing auth token. Set DATASTEAM_API_KEY or use --config with auth.token"
        )


def _run_datsblack(args: argparse.Namespace, settings: FullSettings) -> int:
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

        sink: ActionSink = DryRunActionSink() if args.dry_run else client_action_sink(client)
        loop = RuntimeLoop(
            state_provider=DatsBlackStateProvider(client=client),
            strategy=SafeBaselineStrategy(),
            action_validator=DatsBlackActionValidator(),
            action_sink=sink,
            replay_writer=ReplayWriter(settings.app.runtime.replay_dir),
        )

        outputs = [loop.step() for _ in range(args.ticks)]
        print(json.dumps(outputs, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps({"error": f"Unsupported command: {args.command}"}))
    return 2


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    settings = load_settings(args.config)

    if args.scope == "fixture-run":
        return _run_fixture(args.fixture)
    if args.scope == "datsblack":
        return _run_datsblack(args, settings)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
