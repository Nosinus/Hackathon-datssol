from __future__ import annotations

import json
from pathlib import Path

from games.datsblack.canonical.state import to_canonical
from games.datsblack.models.raw import ScanResponse


def test_to_canonical_maps_entities() -> None:
    raw = json.loads(Path("tests/fixtures/datsblack_scan_sample.json").read_text(encoding="utf-8"))
    scan = ScanResponse.model_validate(raw)
    state = to_canonical(scan).state
    assert state.tick == 101
    assert len(state.me) == 2
    assert state.metadata["zone"] is not None
