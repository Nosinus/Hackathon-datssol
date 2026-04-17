from __future__ import annotations

from datsteam_core.config.settings import load_from_env
from datsteam_core.ops import build_run_manifest


def test_build_run_manifest_has_required_fields(monkeypatch) -> None:
    monkeypatch.setenv("DATASTEAM_API_KEY", "token")
    settings = load_from_env()
    manifest = build_run_manifest(
        settings=settings,
        policy_id="safe_baseline",
        mode="training",
        environment="local",
        git_sha="abc123",
        run_id="r1",
        session_id="s1",
    )

    payload = manifest.as_replay_metadata()
    assert payload["run_id"] == "r1"
    assert payload["session_id"] == "s1"
    assert payload["policy_id"] == "safe_baseline"
    assert payload["config_hash"]
    assert payload["git_sha"] == "abc123"
