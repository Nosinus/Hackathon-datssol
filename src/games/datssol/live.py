from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.cli import _build_datssol_client

from datsteam_core.config.settings import FullSettings, load_from_env, load_from_yaml
from datsteam_core.replay.store import ReplayWriter
from datsteam_core.runtime.loop import RuntimeLoop
from datsteam_core.types.core import ActionEnvelope, ActionSink, CanonicalState, StateProvider
from games.datssol.adapter import DatsSolActionSink, DatsSolStateProvider
from games.datssol.api.client import DatsSolClient
from games.datssol.canonical.state import to_canonical
from games.datssol.models.raw import ArenaResponse
from games.datssol.strategy.baseline import DatsSolBaselineStrategy
from games.datssol.strategy.legal import DatsSolActionValidator


class FixtureArenaProvider:
    def __init__(self, fixture_path: Path) -> None:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        states = payload if isinstance(payload, list) else [payload]
        self._states = [to_canonical(ArenaResponse.model_validate(item)).state for item in states]
        self._idx = 0

    def poll(self) -> CanonicalState:
        if self._idx >= len(self._states):
            return self._states[-1]
        state = self._states[self._idx]
        self._idx += 1
        return state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DatsSol v1 loop")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--ticks", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fixture", type=Path, default=Path("tests/fixtures/datssol/arena_sample.json")
    )
    return parser.parse_args()


def load_settings(config_path: Path | None) -> FullSettings:
    if config_path is None:
        return load_from_env()
    return load_from_yaml(config_path)


def build_client(settings: FullSettings) -> DatsSolClient:
    return _build_datssol_client(settings)


def main() -> None:
    args = parse_args()
    settings = load_settings(args.config)

    if args.dry_run:
        provider: StateProvider = FixtureArenaProvider(args.fixture)
        sink: ActionSink = _DryRunActionSink()
    else:
        client = build_client(settings)
        provider = DatsSolStateProvider(client=client)
        sink = DatsSolActionSink(client=client)

    loop = RuntimeLoop(
        state_provider=provider,
        strategy=DatsSolBaselineStrategy(),
        action_validator=DatsSolActionValidator(),
        action_sink=sink,
        replay_writer=ReplayWriter(settings.app.runtime.replay_dir),
        send_margin_ms=settings.app.runtime.send_margin_ms,
    )
    print(json.dumps([loop.step() for _ in range(args.ticks)], ensure_ascii=False, indent=2))


class _DryRunActionSink:
    def submit(self, action: ActionEnvelope) -> dict[str, object]:
        if not action.payload:
            return {"code": 0, "errors": ["dry-run: skipped submit"]}
        return {"code": 0, "errors": [], "dry_run": True, "payload": action.payload}


if __name__ == "__main__":
    main()
