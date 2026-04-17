from __future__ import annotations

import json
from pathlib import Path

from datsteam_core.replay.store import ReplayWriter
from datsteam_core.runtime.loop import RuntimeLoop
from datsteam_core.types.core import ActionEnvelope, ActionSink, CanonicalState, StateProvider
from games.datsblack.canonical.state import to_canonical
from games.datsblack.models.raw import ScanResponse
from games.datsblack.strategy.baseline import SafeBaselineStrategy
from games.datsblack.strategy.legal import DatsBlackActionValidator


class FixtureStateProvider(StateProvider):
    def __init__(self, fixture_path: Path) -> None:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        self._state: CanonicalState = to_canonical(ScanResponse.model_validate(payload)).state

    def poll(self) -> CanonicalState:
        return self._state


class EchoActionSink(ActionSink):
    def submit(self, action: ActionEnvelope) -> dict[str, object]:
        return {"success": True, "echo": action.payload}


def main() -> None:
    loop = RuntimeLoop(
        state_provider=FixtureStateProvider(Path("tests/fixtures/datsblack_scan_sample.json")),
        strategy=SafeBaselineStrategy(),
        action_validator=DatsBlackActionValidator(),
        action_sink=EchoActionSink(),
        replay_writer=ReplayWriter(Path("logs/replay")),
    )
    print(loop.step())


if __name__ == "__main__":
    main()
