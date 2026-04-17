from __future__ import annotations

from datsteam_core.replay.store import ReplayWriter
from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState


def test_replay_writer_creates_file(tmp_path) -> None:
    writer = ReplayWriter(base_dir=tmp_path)
    state = CanonicalState(
        tick=5,
        me=(CanonicalEntity(id="1", x=1, y=2),),
        enemies=(),
        metadata={},
    )
    action = ActionEnvelope(tick=5, payload={"ships": [{"id": 1}]}, reason="test")
    out = writer.write_step(state, action, {"success": True})
    assert out.exists()
    assert '"tick": 5' in out.read_text(encoding="utf-8")


def test_replay_writer_uses_unique_paths_per_write(tmp_path) -> None:
    writer = ReplayWriter(base_dir=tmp_path)
    state = CanonicalState(
        tick=7,
        me=(CanonicalEntity(id="1", x=1, y=2),),
        enemies=(),
        metadata={},
    )
    action = ActionEnvelope(tick=7, payload={"ships": [{"id": 1}]}, reason="test")

    first = writer.write_step(state, action, {"success": True})
    second = writer.write_step(state, action, {"success": True})

    assert first != second
    assert first.exists()
    assert second.exists()
