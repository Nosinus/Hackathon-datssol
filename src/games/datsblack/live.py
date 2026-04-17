from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from datsteam_core.auth.headers import HeaderTokenAuth
from datsteam_core.config.settings import FullSettings, load_from_env, load_from_yaml
from datsteam_core.replay.store import ReplayWriter
from datsteam_core.runtime.loop import RuntimeLoop
from datsteam_core.transport.http import HttpTransport, RetryPolicy, TransportError
from datsteam_core.types.core import ActionEnvelope, ActionSink
from games.datsblack.adapter import DatsBlackStateProvider
from games.datsblack.api.client import DatsBlackClient
from games.datsblack.api.map_cache import MapCache
from games.datsblack.strategy.baseline import SafeBaselineStrategy
from games.datsblack.strategy.legal import DatsBlackActionValidator


@dataclass
class DryRunActionSink(ActionSink):
    def submit(self, action: ActionEnvelope) -> dict[str, object]:
        return {"success": True, "dry_run": True, "payload": action.payload}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DatsBlack live harness")
    parser.add_argument("--config", type=Path, default=None, help="YAML config path")
    parser.add_argument("--mode", choices=["royal", "deathmatch"], default=None)
    parser.add_argument("--ticks", type=int, default=1, help="number of runtime steps")
    parser.add_argument("--dry-run", action="store_true", help="skip shipCommand submit")
    parser.add_argument("--scan-only", action="store_true", help="only poll scan and exit")
    parser.add_argument("--register", action="store_true", help="call registration endpoint first")
    parser.add_argument("--exit-battle", action="store_true", help="call deathmatch exit at end")
    parser.add_argument(
        "--map-cache", action="store_true", help="fetch /api/map and cache mapUrl blob"
    )
    return parser.parse_args()


def load_settings(config_path: Path | None) -> FullSettings:
    if config_path is None:
        return load_from_env()
    return load_from_yaml(config_path)


def build_client(settings: FullSettings) -> DatsBlackClient:
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
    return DatsBlackClient(transport=transport)


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)
    mode = args.mode or settings.datsblack.mode
    client = build_client(settings)

    try:
        if args.register:
            if mode == "deathmatch":
                print(client.register_deathmatch().model_dump(exclude_none=True))
            else:
                print(client.register_royal().model_dump(exclude_none=True))

        if args.map_cache:
            map_response = client.get_map()
            cache = MapCache(base_dir=settings.datsblack.map_cache_dir)
            out = cache.cache_map_from_response(map_response)
            print(
                {
                    "map": map_response.model_dump(exclude_none=True),
                    "cache_path": str(out) if out else None,
                }
            )

        if args.scan_only:
            print(client.scan().model_dump(exclude_none=True))
            return

        sink: ActionSink
        if args.dry_run:
            sink = DryRunActionSink()
        else:
            sink = client_action_sink(client)

        loop = RuntimeLoop(
            state_provider=DatsBlackStateProvider(client=client),
            strategy=SafeBaselineStrategy(),
            action_validator=DatsBlackActionValidator(),
            action_sink=sink,
            replay_writer=ReplayWriter(settings.app.runtime.replay_dir),
            send_margin_ms=settings.app.runtime.send_margin_ms,
        )

        outputs: list[dict[str, object]] = []
        for _ in range(args.ticks):
            outputs.append(loop.step())
        print(json.dumps(outputs, ensure_ascii=False, indent=2))

        if args.exit_battle and mode == "deathmatch":
            print(client.exit_deathmatch().model_dump(exclude_none=True))

    except TransportError as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "type": exc.__class__.__name__,
                    "method": exc.method,
                    "path": exc.path,
                    "attempt": exc.attempt,
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(2) from exc


def client_action_sink(client: DatsBlackClient) -> ActionSink:
    from games.datsblack.adapter import DatsBlackActionSink

    return DatsBlackActionSink(client=client)


if __name__ == "__main__":
    main()
