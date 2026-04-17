from __future__ import annotations

import json

from datsteam_core.replay.schema import upgrade_legacy_record
from datsteam_core.replay.store import ReplayWriter
from datsteam_core.replay.summary import summarize_replay_dir
from datsteam_core.types.core import ActionEnvelope, CanonicalEntity, CanonicalState


def test_replay_writer_creates_file(tmp_path) -> None:
    writer = ReplayWriter(base_dir=tmp_path, session_id="s1", round_id="r1")
    state = CanonicalState(
        tick=5,
        me=(CanonicalEntity(id="1", x=1, y=2),),
        enemies=(),
        metadata={},
    )
    action = ActionEnvelope(tick=5, payload={"ships": [{"id": 1}]}, reason="test")
    out = writer.write_step(state, action, {"success": True})
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "replay.v2"
    assert payload["server_tick"] == 5
    assert payload["session_id"] == "s1"


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
    second = writer.write_step(state, action, {"success": False})

    assert first != second
    assert first.exists()
    assert second.exists()


def test_replay_summary_supports_v2(tmp_path) -> None:
    writer = ReplayWriter(base_dir=tmp_path)
    s1 = CanonicalState(tick=1, me=(CanonicalEntity(id="1", x=0, y=0),), enemies=(), metadata={})
    s2 = CanonicalState(tick=2, me=(CanonicalEntity(id="1", x=1, y=0),), enemies=(), metadata={})
    a = ActionEnvelope(tick=1, payload={"ships": [{"id": 1}]}, reason="test")

    writer.write_step(s1, a, {"success": True})
    writer.write_step(
        s2,
        a,
        {"success": False},
        fallback_flags={"deterministic_fallback": True},
        parser_extras={"unknown_fields": ["foo", "bar"]},
    )

    summary = summarize_replay_dir(tmp_path)
    assert summary.files == 2
    assert summary.tick_min == 1
    assert summary.tick_max == 2
    assert summary.non_success_results == 1
    assert summary.fallback_count == 1
    assert summary.parser_unknown_field_count == 2


def test_upgrade_legacy_replay_payload() -> None:
    envelope = upgrade_legacy_record(
        {
            "tick": 8,
            "state": {"tick": 8, "me": [], "enemies": [], "metadata": {}},
            "action": {"ships": []},
            "reason": "legacy",
            "result": {"success": True},
        }
    )

    assert envelope.schema_version == "replay.v2"
    assert envelope.server_tick == 8
    assert envelope.validation_flags["upgraded_from_legacy"] is True
